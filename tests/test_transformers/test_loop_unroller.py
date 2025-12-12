# tests/test_transformers/test_loop_unroller.py
import pytest

from haproxy_translator.parsers import DSLParser
from haproxy_translator.utils.errors import ParseError


def test_loop_unrolling_with_variables():
    """Test that loops can use variables in their range."""
    dsl_source = """
config loop_unroll_vars {
    let num_servers = 3

    backend web_servers {
        balance: roundrobin

        servers {
            for i in [1..${num_servers}] {
                server "web-${i}" {
                    address: "192.168.1.${i}"
                    port: 80
                    check: true
                }
            }
        }
    }
}
"""
    parser = DSLParser()
    ir = parser.parse(dsl_source)

    assert len(ir.backends) == 1
    backend = ir.backends[0]
    assert backend.name == "web_servers"

    assert len(backend.servers) == 3
    assert backend.servers[0].name == "web-1"
    assert backend.servers[0].address == "192.168.1.1"
    assert backend.servers[1].name == "web-2"
    assert backend.servers[1].address == "192.168.1.2"
    assert backend.servers[2].name == "web-3"
    assert backend.servers[2].address == "192.168.1.3"


def test_loop_unrolling_with_undefined_variable():
    """Test that loop unrolling fails with an undefined variable."""
    dsl_source = """
config loop_unroll_vars {
    backend web_servers {
        balance: roundrobin

        servers {
            for i in [1..${num_servers}] {
                server "web-${i}" {
                    address: "192.168.1.${i}"
                    port: 80
                }
            }
        }
    }
}
"""
    parser = DSLParser()
    with pytest.raises(ParseError, match="Failed to evaluate expression 'num_servers'"):
        parser.parse(dsl_source)


def test_loop_unrolling_with_expression_in_range():
    """Test that loops can use expressions in their range."""
    dsl_source = """
config loop_unroll_vars {
    let num_servers = 3

    backend web_servers {
        balance: roundrobin

        servers {
            for i in [1..${num_servers + 1}] {
                server "web-${i}" {
                    address: "192.168.1.${i}"
                    port: 80
                    check: true
                }
            }
        }
    }
}
"""
    parser = DSLParser()
    ir = parser.parse(dsl_source)

    assert len(ir.backends) == 1
    backend = ir.backends[0]
    assert len(backend.servers) == 4
    assert backend.servers[3].name == "web-4"
