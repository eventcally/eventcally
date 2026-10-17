class SubTests:
    def call_sub_tests(self):
        sub_tests = [
            getattr(self, method_name)
            for method_name in dir(self)
            if callable(getattr(self, method_name)) and method_name.startswith("_test")
        ]

        for sub_test in sub_tests:
            sub_test()
