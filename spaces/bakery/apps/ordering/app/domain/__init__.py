"""Pure business domain for the bakery: products, cart, orders, session state.

Nothing in this package knows about HTTP, MCP, or ChatGPT. It is deliberately
transport-agnostic so the same logic could power a REST API, a CLI, or tests.
"""
