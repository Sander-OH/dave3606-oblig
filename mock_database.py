class MockDatabase:
    def execute_and_fetch_all(self, query, params=None):

        # Mock for: get ONE set (has WHERE)
        if "FROM lego_set" in query and "WHERE" in query:
            assert params == ("123",)
            return [
                ("Test Set", 2020, "Test Category", "test.png")
            ]

        # Mock for: get ALL sets (no WHERE)
        if "FROM lego_set" in query:
            return [
                ("123", "Test Set"),
                ("456", "Another Set")
            ]
        
        # Mock for: inventory query
        if "FROM lego_inventory" in query:
            assert params == ("123",)
            return [
                ("3001", 5, "Brick 2x4", "brick.png", 4),
                ("3002", 1, "Brick 2x3", "brick2.png", 2)
            ]

        return []

    def close(self):
        pass