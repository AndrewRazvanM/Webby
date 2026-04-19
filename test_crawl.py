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
            '<a href="https://crawler-test.com/about">About</a>',           # T0
            '<a href="/about">About</a>',                                    # T1
            '<a href="https://crawler-test.com/contact">Contact</a>',       # T2
            '<a href="https://crawler-test.com/../up">Up</a>',              # T3
            '<a href="https://crawler-test.com#section">Section</a>',       # T4: fragment stripped → root
            '<a href="">Empty</a>',                                          # T5
            '<a>No link</a>',                                               # T6
            '<a href="https://crawler-test.com/a">A</a><a href="https://crawler-test.com/b">B</a>',  # T7
            '<a href="https://crawler-test.com/dup">1</a><a href="https://crawler-test.com/dup">2</a>',  # T8: dedup
            '<a href="https://crawler-test.com">Home</a>',                  # T9
            '<a href="https://crawler-test.com/lib.js">CDN</a>',            # T10
            '<a href="https://crawler-test.com/search?q=test">Search</a>',  # T11
            '<a href="javascript:void(0)">Click</a>',                       # T12: dropped
            '<a href="mailto:test@example.com">Email</a>',                  # T13: dropped
            '''
            <a href="https://crawler-test.com/valid">Valid</a>
            <a href="javascript:void(0)">JS</a>
            <a>No href</a>
            ''',                                                             # T14: js dropped
            '<A HREF="https://crawler-test.com/upper">Upper</A>',           # T15: uppercase handled
            '<a href="https://crawler-test.com/broken">Broken',             # T16: unclosed tag
            '<div><a href="https://crawler-test.com/nested"><span>Text</span></a></div>',  # T17
            '<a href="https://crawler-test.com/page#section">Fragment</a>', # T18: fragment stripped
        ]
        expected = [
            ["https://crawler-test.com/about"],        # T0
            ["https://crawler-test.com/about"],        # T1
            ["https://crawler-test.com/contact"],      # T2
            ["https://crawler-test.com/../up"],        # T3
            ["https://crawler-test.com/"],             # T4: fragment stripped, root URL
            [],                                        # T5
            [],                                        # T6
            ["https://crawler-test.com/a", "https://crawler-test.com/b"],  # T7
            ["https://crawler-test.com/dup"],          # T8
            ["https://crawler-test.com"],              # T9
            ["https://crawler-test.com/lib.js"],       # T10
            ["https://crawler-test.com/search?q=test"],# T11
            [],                                        # T12: javascript: dropped
            [],                                        # T13: mailto: dropped
            ["https://crawler-test.com/valid"],        # T14: js dropped
            ["https://crawler-test.com/upper"],        # T15
            ["https://crawler-test.com/broken"],       # T16
            ["https://crawler-test.com/nested"],       # T17
            ["https://crawler-test.com/page"],         # T18: fragment stripped
        ]
        base_url = "https://crawler-test.com"
        for idx, test in enumerate(input_body):
            with self.subTest(test=test):
                actual = get_urls_from_html(test, base_url)
                self.assertEqual(actual, expected[idx], f"\nTest {idx} failed")

    def test_get_images_from_html(self):
        input_body = [
            '<img src="https://crawler-test.com/a.png">',                   # T0
            '<img src="/about.png">',                                        # T1: relative → absolute
            '<img src="about.png">',                                         # T2: no leading slash → resolved
            '<img src="https://crawler-test.com/a.png"><img src="https://crawler-test.com/b.png">',  # T3
            '<img src="https://crawler-test.com/a.png"><img src="https://crawler-test.com/a.png">',  # T4: dedup
            '<img src="">',                                                   # T5
            '<img>',                                                          # T6
            '<IMG SRC="https://crawler-test.com/upper.png">',               # T7: uppercase attrs
            '<img data-src="https://crawler-test.com/lazy.png">',           # T8: data-src ignored
            '<img srcset="https://crawler-test.com/srcset.png 1x">',        # T9: srcset resolved
            '<img src="//cdn.crawler-test.com/cdn.png">',                   # T10: protocol-relative
            '<img src="data:image/png;base64,AAAA">',                       # T11: data URI dropped
            '<div><img src="https://crawler-test.com/nested.png"></div>',   # T12
            '<img src="https://crawler-test.com/query.png?x=1&y=2">',      # T13: query string preserved
            '<img src="https://crawler-test.com/page.png#section">',        # T14: fragment stripped
            '<img src="   https://crawler-test.com/space.png   ">',         # T15: whitespace stripped
        ]
        expected = [
            ["https://crawler-test.com/a.png"],        # T0
            ["https://crawler-test.com/about.png"],    # T1
            ["https://crawler-test.com/about.png"],    # T2: urljoin resolves relative paths
            ["https://crawler-test.com/a.png", "https://crawler-test.com/b.png"],  # T3
            ["https://crawler-test.com/a.png"],        # T4
            [],                                        # T5
            [],                                        # T6
            ["https://crawler-test.com/upper.png"],    # T7
            [],                                        # T8: data-src not read
            ["https://crawler-test.com/srcset.png"],   # T9
            ["https://cdn.crawler-test.com/cdn.png"],  # T10
            [],                                        # T11
            ["https://crawler-test.com/nested.png"],   # T12
            ["https://crawler-test.com/query.png?x=1&y=2"],  # T13
            ["https://crawler-test.com/page.png"],     # T14: fragment stripped
            ["https://crawler-test.com/space.png"],    # T15
        ]

        base_url = "https://crawler-test.com"
        for idx, test in enumerate(input_body):
            with self.subTest(test=test):
                actual = get_images_from_html(test, base_url)
                self.assertEqual(actual, expected[idx], f"\nTest {idx} failed")

if __name__ == "__main__":
    unittest.main()