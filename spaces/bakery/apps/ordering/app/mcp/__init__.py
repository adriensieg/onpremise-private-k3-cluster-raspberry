"""MCP integration layer.

Two responsibilities, deliberately kept apart:

  * `factory`  — the MCP Application Factory: builds a fresh `Server` for a
                 session and registers its tools, resources, and widgets. It
                 knows nothing about HTTP or sessions.
  * `runtime`  — the Runtime Hosting Layer: owns the streamable-HTTP transport,
                 session lifecycle, and request routing. It knows nothing about
                 pastries.

`tools`, `resources`, and `metadata` are used by the factory.
"""
