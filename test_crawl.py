import unittest
from crawl import normalize_urls, get_heading_from_html, get_first_paragraph_from_html, get_urls_from_html, get_images_from_html


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

    def test_get_urls_from_html_absolute(self):
        input_body = [
            '<a href="https://crawler-test.com/about">About</a>',
            '<a href="/about">About</a>',
            '<a href="https://crawler-test.com/contact">Contact</a>',
            '<a href="https://crawler-test.com/../up">Up</a>',
            '<a href="https://crawler-test.com#section">Section</a>',
            '<a href="">Empty</a>',
            '<a>No link</a>',
            '<a href="https://crawler-test.com/a">A</a><a href="https://crawler-test.com/b">B</a>',
            '<a href="https://crawler-test.com/dup">1</a><a href="https://crawler-test.com/dup">2</a>',
            '<a href="https://crawler-test.com">Home</a>',
            '<a href="https://crawler-test.com/lib.js">CDN</a>',
            '<a href="https://crawler-test.com/search?q=test">Search</a>',
            '<a href="javascript:void(0)">Click</a>',
            '<a href="mailto:test@example.com">Email</a>',
            '''
            <a href="https://crawler-test.com/valid">Valid</a>
            <a href="javascript:void(0)">JS</a>
            <a>No href</a>
            ''',
            '<A HREF="https://crawler-test.com/upper">Upper</A>',
            '<a href="https://crawler-test.com/broken">Broken',
            '<div><a href="https://crawler-test.com/nested"><span>Text</span></a></div>',
            '<a href="https://crawler-test.com/page#section">Fragment</a>',
        ]
        expected = [
            ["https://crawler-test.com/about"],
            ["https://crawler-test.com/about"],
            ["https://crawler-test.com/contact"],
            ["https://crawler-test.com/../up"],
            ["https://crawler-test.com#section"],
            [],
            [],
            ["https://crawler-test.com/a", "https://crawler-test.com/b"],
            ["https://crawler-test.com/dup"],
            ["https://crawler-test.com"],
            ["https://crawler-test.com/lib.js"],
            ["https://crawler-test.com/search?q=test"],
            ["javascript:void(0)"],
            ["mailto:test@example.com"],
            ["https://crawler-test.com/valid", "javascript:void(0)"],
            ["https://crawler-test.com/upper"],
            ["https://crawler-test.com/broken"],
            ["https://crawler-test.com/nested"],
            ["https://crawler-test.com/page#section"],
        ]
        base_url = "https://crawler-test.com"
        for idx, test in enumerate(input_body):
            with self.subTest(test=test):
                actual = get_urls_from_html(test, base_url)
                self.assertEqual(actual, expected[idx])

    def test_get_images_from_html(self):
        input_body = [
            '<img src="https://crawler-test.com/a.png">',

            '<img src="/about.png">',

            '<img src="about.png">',

            '<img src="https://crawler-test.com/a.png"><img src="https://crawler-test.com/b.png">',

            '<img src="https://crawler-test.com/a.png"><img src="https://crawler-test.com/a.png">',

            '<img src="">',

            '<img>',

            '<IMG SRC="https://crawler-test.com/upper.png">',

            '<img data-src="https://crawler-test.com/lazy.png">',

            '<img srcset="https://crawler-test.com/srcset.png 1x">',

            '<img src="//cdn.crawler-test.com/cdn.png">',

            '<img src="data:image/png;base64,AAAA">',

            '<div><img src="https://crawler-test.com/nested.png"></div>',

            '<img src="https://crawler-test.com/query.png?x=1&y=2">',

            '<img src="https://crawler-test.com/page.png#section">',

            '<img src="   https://crawler-test.com/space.png   ">',
        ]
        expected = [
            ["https://crawler-test.com/a.png"],

            ["https://crawler-test.com/about.png"],

            [],

            ["https://crawler-test.com/a.png", "https://crawler-test.com/b.png"],

            ["https://crawler-test.com/a.png"],

            [],

            [],

            ["https://crawler-test.com/upper.png"],

            [],

            [],

            ["https://cdn.crawler-test.com/cdn.png"],

            [],

            ["https://crawler-test.com/nested.png"],

            ["https://crawler-test.com/query.png?x=1&y=2"],

            ["https://crawler-test.com/page.png#section"],

            ["https://crawler-test.com/space.png"],
        ]

        base_url = "https://crawler-test.com"
        for idx, test in enumerate(input_body):
            with self.subTest(test=test):
                actual = get_images_from_html(test, base_url)
                self.assertEqual(actual, expected[idx], f"\nTest {idx} failed")

if __name__ == "__main__":
    unittest.main()