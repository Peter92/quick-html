"""Quick and easy way of building HTML code through context managers.
This is a simple module so there is no validation or special cases.

Example:
    <html>
        <head>
            <title>My Webpage</title>
            <link href="style.css" rel="stylesheet"/>
        </head>
    </html>

    with QuickHtml() as web:
        with web.html():
            with web.head():
                web.title()('My Webpage')
                web.link(href='style.css', rel='stylesheet')
"""


def reserved(word):
    """Parse for any reserved words.
    This is needed for words such as "class", which is used in html but
    reserved in Python.
    The convention is to use "word_" instead.
    """
    if word == 'class_':
        return 'class'
    return word


class Element(object):
    __slots__ = ('indent', 'is_context_manager', 'parent', 'text')

    def __init__(self, **kwargs):
        """Initialise the class and write the element as if it's closed."""

        self.indent = ' ' * self.parent._indent * self.parent._depth
        self.text = []
        self.parent._previous = self
        self.is_context_manager = False

        # Write opening element
        if kwargs:
            params = ' '.join('{}={}'.format(reserved(k), v.__repr__()) for k, v in kwargs.items())
            self.parent._lines.append('{}<{} {}/>'.format(self.indent, self.__class__.__name__, params))
        else:
            self.parent._lines.append('{}<{}/>'.format(self.indent, self.__class__.__name__))

    def __enter__(self):
        """Modify element to make it open."""

        self.is_context_manager = True
        self.parent._lines[-1] = self.parent._lines[-1][:-2] + self.parent._lines[-1][-1]  # Swap "/>" for ">"
        self.parent._depth += 1

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Write any text and a closing element."""
        
        if self.text:
            text = '<br/>'.join(self.text)
            if len(self.text) > 1:
                with self.parent.p() as paragraph:
                    paragraph(text)
            else:
                indent = ' ' * (self.parent._indent * self.parent._depth)
                self.parent._lines.append(indent + text.replace('<br/>', '\n{i}<br/>\n{i}'.format(i=indent)))

        self.parent._depth -= 1
        self.parent._lines.append('{}</{}>'.format(self.indent, self.__class__.__name__))
    
    def __call__(self, text):
        """Add text into the element."""

        self.text.append(text)

        # Force call to correctly apply text
        if not self.is_context_manager:
            self.__enter__()
            self.__exit__(None, None, None)


class QuickHtml(object):
    def __init__(self, indent=2):
        self._indent = indent
        self._lines = []
        self._previous = None
        self._depth = 0
        self._cls_cache = {}
        self._html = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cache the html code."""

        self._html = '\n'.join(self._lines)

    def __getattr__(self, attr):
        """Dynamically generate a class from Element."""

        if attr in self._cls_cache:
            return self._cls_cache[attr]
        self._cls_cache[attr] = type(attr, (Element,), {'parent': self})
        return self._cls_cache[attr]
    
    def __call__(self, text):
        """Add text to the previous element."""

        self._previous.text.append(text)

    def __str__(self):
        """Display page as html.
        This will raise an error if called before the generation is finished.
        """

        if self._html is None:
            raise RuntimeError('code is not ready to display')
        return self._html


if __name__ == '__main__':
    example = '''<html lang="en">
    <head>
        <title>
            Python Flask Bucket List App
        </title>
        <link href="http://getbootstrap.com/dist/css/bootstrap.min.css" rel="stylesheet"/>
        <link href="http://getbootstrap.com/examples/jumbotron-narrow/jumbotron-narrow.css" rel="stylesheet"/>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <nav>
                    <ul class="nav nav-pills pull-right">
                        <li role="presentation" class="active">
                            <a href="#">
                                Home
                            </a>
                        </li>
                        <li role="presentation">
                            <a href="#">
                                Sign In
                            </a>
                        </li>
                        <li role="presentation">
                            <a href="#">
                                Sign Up
                            </a>
                        </li>
                    </ul>
                </nav>
                <h3 class="text-muted">
                    Python Flask App
                </h3>
            </div>
        </div>
    </body>
</html>'''

    with QuickHtml(indent=4) as web:
        with web.html(lang='en'):
            with web.head():
                web.title()('Python Flask Bucket List App')
                web.link(href='http://getbootstrap.com/dist/css/bootstrap.min.css', rel='stylesheet')
                web.link(href='http://getbootstrap.com/examples/jumbotron-narrow/jumbotron-narrow.css', rel='stylesheet')
            with web.body():
                with web.div(class_='container'):
                    with web.div(class_='header'):
                        with web.nav():
                            with web.ul(class_='nav nav-pills pull-right'):
                                for i, item in enumerate(('Home', 'Sign In', 'Sign Up')):
                                    if i:
                                        kwargs = {}
                                    else:
                                        kwargs = {'class_': 'active'}
                                    with web.li(role='presentation', **kwargs):
                                        web.a(href='#')(item)
                        web.h3(class_='text-muted')('Python Flask App')

    assert str(web) == example.replace('"', "'")
