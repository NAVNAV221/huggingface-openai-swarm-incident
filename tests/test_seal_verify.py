import errno
import importlib.util
import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).parents[1] / "lab/sandbox/seal_verify.py"
SPEC = importlib.util.spec_from_file_location("seal_verify", MODULE)
seal = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = seal
SPEC.loader.exec_module(seal)


class DenialTests(unittest.TestCase):
    def test_route_denial_passes(self):
        passed, _ = seal.classify_denial(OSError(errno.ENETUNREACH, "no route"))
        self.assertTrue(passed)

    def test_policy_denial_passes(self):
        passed, _ = seal.classify_denial(PermissionError(errno.EPERM, "policy"))
        self.assertTrue(passed)

    def test_timeout_is_inconclusive_and_fails(self):
        passed, detail = seal.classify_denial(socket.timeout("timeout"))
        self.assertFalse(passed)
        self.assertIn("INCONCLUSIVE", detail)

    @patch("socket.socket")
    def test_disabled_ipv6_error_passes_only_ipv6_probe(self, socket_factory):
        socket_factory.return_value.connect.side_effect = OSError(errno.EADDRNOTAVAIL, "disabled")
        self.assertTrue(seal.denied_probe("v6", "2606:4700:4700::1111", 443, ipv6=True).passed)
        self.assertFalse(seal.denied_probe("v4", "1.1.1.1", 443).passed)

    def test_connection_refused_does_not_prove_remote_seal(self):
        passed, _ = seal.classify_denial(ConnectionRefusedError(errno.ECONNREFUSED, "refused"))
        self.assertFalse(passed)

    @patch("socket.socket")
    def test_successful_raw_ip_connection_fails(self, socket_factory):
        socket_factory.return_value.connect.return_value = None
        result = seal.denied_probe("raw", "1.1.1.1", 443)
        self.assertFalse(result.passed)
        self.assertIn("UNSEALED", result.detail)

    @patch("socket.socket")
    def test_raw_ip_timeout_fails(self, socket_factory):
        socket_factory.return_value.connect.side_effect = socket.timeout("timeout")
        self.assertFalse(seal.denied_probe("raw", "1.1.1.1", 443).passed)


class PositiveControlTests(unittest.TestCase):
    @patch.dict("os.environ", {"DEPOT_TOKEN": "test"}, clear=False)
    @patch("seal_verify.request", return_value=(200, b'{"paths":["a/b"]}'))
    def test_flat_depot_control_passes(self, _request):
        self.assertTrue(seal.positive_control().passed)

    @patch("seal_verify.request", return_value=(200, b'{"paths":[],"authors":[]}'))
    def test_author_feed_is_not_accepted_as_flat_control(self, _request):
        self.assertFalse(seal.positive_control().passed)

    @patch("seal_verify.request", side_effect=socket.timeout("timeout"))
    def test_dead_positive_control_fails(self, _request):
        self.assertFalse(seal.positive_control().passed)

    def test_remote_model_url_fails_without_network(self):
        self.assertFalse(seal.model_control("https://api.openai.com/v1").passed)

    @patch("seal_verify.request", return_value=(404, b"{}"))
    def test_disallowed_proxy_route_passes_only_on_404(self, _request):
        self.assertTrue(seal.proxy_route_control("/v1/models").passed)

    @patch("seal_verify.request", return_value=(200, b"{}"))
    def test_open_proxy_route_fails(self, _request):
        self.assertFalse(seal.proxy_route_control("/v1/models").passed)


class DnsTests(unittest.TestCase):
    @patch("seal_verify.dns_query", return_value=(3, 0, b""))
    def test_nxdomain_passes(self, _query):
        self.assertTrue(seal.check_nxdomain("172.30.0.53", "nonce.invalid").passed)

    @patch("seal_verify.dns_query", return_value=(0, 0, b""))
    def test_empty_noerror_does_not_impersonate_nxdomain(self, _query):
        self.assertFalse(seal.check_nxdomain("172.30.0.53", "nonce.invalid").passed)

    @patch("seal_verify.dns_query", side_effect=socket.timeout("timeout"))
    def test_dns_timeout_fails(self, _query):
        self.assertFalse(seal.check_nxdomain("172.30.0.53", "nonce.invalid").passed)


if __name__ == "__main__":
    unittest.main()
