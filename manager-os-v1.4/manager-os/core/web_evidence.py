"""Bounded public-page retrieval. Page text is evidence, never an instruction.

Connections are made directly to a vetted numeric address, with the URL's host
retained for TLS verification and the HTTP Host header. No cookies, credentials,
proxies, JavaScript, account sessions, or search-engine claims are involved.
"""
import asyncio
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import http.client
import ipaddress
import re
import socket
import ssl
import threading
import time
from urllib.parse import parse_qsl, urljoin, urlsplit, urlunsplit


MAX_BYTES = 512 * 1024
MAX_TEXT = 30000
MAX_REDIRECTS = 3
TOTAL_TIMEOUT = 20.0
READ_TIMEOUT = 6.0
CONTENT_TYPES = {'text/html', 'application/xhtml+xml', 'text/plain', 'application/json', 'text/markdown'}


class PublicPageError(ValueError):
    """The URL could not be retrieved within the public-page tool's limits."""


def _public_ip(value):
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise PublicPageError('The server address is invalid.') from exc
    if (not address.is_global or address.is_multicast or address.is_reserved
            or address.is_unspecified or address.is_loopback or address.is_link_local
            or (isinstance(address, ipaddress.IPv6Address) and (
                address.ipv4_mapped is not None or address.sixtofour is not None
                or address.teredo is not None))):
        raise PublicPageError('Only publicly routable server addresses are allowed.')
    return address


def _url_parts(url):
    if not isinstance(url, str) or not url or len(url) > 4096:
        raise PublicPageError('Provide a public HTTP or HTTPS URL of at most 4096 characters.')
    if re.search(r'[\x00-\x20\x7f\\]', url):
        raise PublicPageError('The URL contains invalid characters.')
    try:
        parts = urlsplit(url)
        host = parts.hostname
        port = parts.port
    except ValueError as exc:
        raise PublicPageError('The URL is malformed.') from exc
    if parts.scheme.lower() not in {'http', 'https'} or not host:
        raise PublicPageError('Only public HTTP or HTTPS pages are supported.')
    if parts.username is not None or parts.password is not None:
        raise PublicPageError('URLs containing account credentials are not supported.')
    sensitive_parameters = {'key', 'apikey', 'token', 'accesstoken', 'refreshtoken',
                            'auth', 'authorization', 'password', 'passwd', 'secret',
                            'signature', 'sig', 'xamzsignature', 'xamzcredential',
                            'xgoogsignature', 'xgoogcredential'}
    if any(re.sub(r'[-_]', '', name.lower()) in sensitive_parameters
           for name, _value in parse_qsl(parts.query, keep_blank_values=True)):
        raise PublicPageError('URLs containing credential query parameters are not supported.')
    if '%' in host:
        raise PublicPageError('Encoded or scoped server names are not supported.')
    try:
        host = host.encode('idna').decode('ascii').rstrip('.').lower()
    except UnicodeError as exc:
        raise PublicPageError('The server name is invalid.') from exc
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if (len(host) > 253 or '.' not in host or not all(
                re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label)
                for label in host.split('.'))):
            raise PublicPageError('The server must have a valid public domain name or address.')
    else:
        _public_ip(host)
    port = port or (443 if parts.scheme.lower() == 'https' else 80)
    if port not in {80, 443}:
        raise PublicPageError('Public-page retrieval supports ports 80 and 443 only.')
    authority = '[' + host + ']' if ':' in host else host
    if port != (443 if parts.scheme.lower() == 'https' else 80):
        authority += ':' + str(port)
    normalized = urlunsplit((parts.scheme.lower(), authority, parts.path or '/', parts.query, ''))
    return normalized, host, port


def _resolve(host, port):
    try:
        entries = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        raise PublicPageError('The public server name could not be resolved.') from exc
    addresses = []
    for family, socktype, protocol, _name, sockaddr in entries:
        if family not in {socket.AF_INET, socket.AF_INET6}:
            raise PublicPageError('The server uses an unsupported address family.')
        _public_ip(sockaddr[0])
        if sockaddr[1] != port or (family == socket.AF_INET6 and sockaddr[3]):
            raise PublicPageError('The server returned an unexpected network endpoint.')
        endpoint = (family, socktype, protocol, sockaddr)
        if endpoint not in addresses:
            addresses.append(endpoint)
    if not addresses:
        raise PublicPageError('The public server has no usable addresses.')
    return addresses


def _remaining(deadline):
    left = deadline - time.monotonic()
    if left <= 0:
        raise PublicPageError('Public-page retrieval exceeded its time limit.')
    return min(READ_TIMEOUT, left)


class _PinnedConnection(http.client.HTTPConnection):
    def __init__(self, host, port, endpoints, secure, deadline):
        super().__init__(host, port, timeout=_remaining(deadline))
        self.endpoints, self.secure, self.deadline = endpoints, secure, deadline
        self.network_socket = None

    def connect(self):
        last_error = None
        for family, socktype, protocol, sockaddr in self.endpoints:
            connection = socket.socket(family, socktype, protocol)
            try:
                self.network_socket = connection
                connection.settimeout(_remaining(self.deadline))
                # sockaddr contains a validated numeric IP, never a DNS name.
                connection.connect(sockaddr)
                if self.secure:
                    context = ssl.create_default_context()
                    connection = context.wrap_socket(connection, server_hostname=self.host)
                    self.network_socket = connection
                _remaining(self.deadline)
                self.sock = connection
                return
            except (OSError, PublicPageError) as exc:
                connection.close()
                last_error = exc
        raise PublicPageError('A verified connection to the public server could not be established.') from last_error

    def abort(self):
        # HTTPConnection may relinquish sock while HTTPResponse still owns its
        # buffered reader. Shutdown also interrupts that reader at the deadline.
        connection = self.network_socket
        if connection is not None:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()


class _PageText(HTMLParser):
    BLOCKS = {'p', 'div', 'section', 'article', 'header', 'footer', 'main', 'aside',
              'li', 'ul', 'ol', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr', 'pre'}
    HIDDEN = {'script', 'style', 'noscript', 'template', 'svg'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden, self.title_depth = [], 0
        self.title, self.text = [], []

    def handle_starttag(self, tag, attrs):
        if tag in self.HIDDEN:
            self.hidden.append(tag)
        if self.hidden:
            return
        if tag == 'title':
            self.title_depth += 1
        if tag in self.BLOCKS:
            self.text.append('\n')

    def handle_startendtag(self, tag, attrs):
        if tag == 'br' and not self.hidden:
            self.text.append('\n')

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        if tag == 'title':
            self.title_depth = max(0, self.title_depth - 1)
        if tag in self.BLOCKS:
            self.text.append('\n')

    def handle_data(self, data):
        if not self.hidden:
            (self.title if self.title_depth else self.text).append(data)


def _extract(raw, content_type, charset):
    try:
        decoded = raw.decode(charset or 'utf-8', errors='replace')
    except LookupError:
        decoded = raw.decode('utf-8', errors='replace')
    title = ''
    if content_type in {'text/html', 'application/xhtml+xml'}:
        parser = _PageText()
        parser.feed(decoded)
        title = ' '.join(''.join(parser.title).split())[:300]
        decoded = ''.join(parser.text)
    lines = [' '.join(line.split()) for line in decoded.splitlines()]
    extracted = '\n'.join(line for line in lines if line)
    return title, extracted[:MAX_TEXT], len(extracted) > MAX_TEXT


def _fetch(url):
    deadline = time.monotonic() + TOTAL_TIMEOUT
    for redirects in range(MAX_REDIRECTS + 1):
        normalized, host, port = _url_parts(url)
        endpoints = _resolve(host, port)
        _remaining(deadline)
        parts = urlsplit(normalized)
        connection = _PinnedConnection(host, port, endpoints, parts.scheme == 'https', deadline)
        timer = threading.Timer(max(0.001, deadline - time.monotonic()), connection.abort)
        timer.daemon = True
        timer.start()
        response = None
        try:
            path = parts.path + ('?' + parts.query if parts.query else '')
            connection.request('GET', path, headers={
                'Host': parts.netloc, 'User-Agent': 'Manager-PublicPage/1.0',
                'Accept': 'text/html, text/plain, application/json;q=0.9',
                'Accept-Encoding': 'identity', 'Connection': 'close'})
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader('Location')
                if not location or redirects == MAX_REDIRECTS:
                    raise PublicPageError('The page has an invalid or excessive redirect chain.')
                url = urljoin(normalized, location)
                continue
            if not 200 <= response.status < 300:
                raise PublicPageError('The public server returned HTTP ' + str(response.status) + '.')
            content_type = response.headers.get_content_type().lower()
            if content_type not in CONTENT_TYPES:
                raise PublicPageError('This URL is not a supported HTML, plain-text, or JSON page.')
            if response.getheader('Content-Encoding', 'identity').strip().lower() not in {'', 'identity'}:
                raise PublicPageError('Compressed page responses are not supported by this bounded reader.')
            body = bytearray()
            while len(body) <= MAX_BYTES:
                if connection.network_socket is not None:
                    connection.network_socket.settimeout(_remaining(deadline))
                else:
                    _remaining(deadline)
                chunk = response.read1(min(16384, MAX_BYTES + 1 - len(body)))
                if not chunk:
                    break
                body.extend(chunk)
            title, extracted, text_truncated = _extract(
                bytes(body[:MAX_BYTES]), content_type, response.headers.get_content_charset())
            return {'url': normalized, 'title': title, 'text': extracted,
                    'retrieved_at': datetime.now(timezone.utc).isoformat(),
                    'sha256': hashlib.sha256(extracted.encode('utf-8')).hexdigest(),
                    'truncated': len(body) > MAX_BYTES or text_truncated}
        except PublicPageError:
            raise
        except (OSError, http.client.HTTPException, ValueError) as exc:
            raise PublicPageError('The public page could not be read within the connection limits.') from exc
        finally:
            timer.cancel()
            if response is not None:
                response.close()
            connection.close()
            connection.abort()
    raise PublicPageError('The page has too many redirects.')


async def fetch_public_page(url):
    """Return sourced, untrusted page text; raise PublicPageError on failure.

    The hash identifies the returned normalized text, not the full remote file.
    DNS and blocking socket I/O run off the event loop; the deadline covers all
    redirects. A stalled OS DNS query may outlive the caller, but a late result
    cannot trigger a subsequent connection after the deadline.
    """
    _url_parts(url)
    try:
        return await asyncio.wait_for(asyncio.to_thread(_fetch, url), timeout=TOTAL_TIMEOUT + 1)
    except asyncio.TimeoutError as exc:
        raise PublicPageError('Public-page retrieval exceeded its time limit.') from exc
