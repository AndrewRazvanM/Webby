import unittest
from crawl import normalize_urls, get_heading_from_html, get_first_paragraph_from_html


class TestCrawl(unittest.TestCase):
    def test_normalized_url(self):
        input_urls = ["https://www.boot.dev/blog/path", 
                      "https://www.boot.dev/blog/path/",
                      "http://www.boot.dev/blog/path/",
                      "http://www.boot.dev/blog/path",
                      "www.boot.dev/blog/path",
        ]
                      
        expected = "www.boot.dev/blog/path"
        for test in input_urls:
            with self.subTest(test=test):
                actual = normalize_urls(test)
                self.assertEqual(actual, expected)

    def test_get_heading_from_html_basic(self):
        input_body = [
            '<html><body><h1>Test Title</h1></body></html>',
            '<html><body><h2>Test Title</h1></body></html>',
            '<html><body><h1>Test Title</h2></body></html>',
            '<html><body><h2>Test Title</h2></body></html>',
            '<html><body><h1>Test Title</h1</body></html>',
            '<html><body><h1>Test Title<h1></body></html>',
        ]

        expected = "Test Title"
        for test in input_body:
            with self.subTest(test=test):
                actual = get_heading_from_html(test)
                self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_main_priority(self):
        input_body = [
        '''<html><body>
            <p>Outside paragraph.</p>
            <main>
                <p>Main paragraph.</p>
            </main>
        </body></html>''',

        '''<html><body>
            <p>Main paragraph.</p>
        </body></html>''',

        '''<html><head><title>The Dormouse's story</title></head>
        <body>
        <p class="title"><b>Main paragraph.</b></p>

        <p class="story">Once upon a time there were three little sisters; and their names were
        <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
        <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
        <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
        and they lived at the bottom of a well.</p>

        <p class="story">...</p>
        ''',

        '''<html><body>
            <main>
                <div>No paragraph here</div>
            </main>
            <p>Main paragraph.</p>
        </body></html>
        ''',

        '''<html><body>
            <main>
                <div>
                    <section>
                        <p>Main paragraph.</p>
                    </section>
                </div>
            </main>
        </body></html>
        '''
        ]

        expected = "Main paragraph."
        for test in input_body:
            with self.subTest(test=test):
                actual = get_first_paragraph_from_html(test)
                self.assertEqual(actual, expected)

if __name__ == "__main__":
    unittest.main()