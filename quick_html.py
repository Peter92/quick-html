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
    IndentSpacing = 4

    def __init__(self, **kwargs):
        self.indent = ' ' * Element.IndentSpacing * Element.Depth
        self._context_manager = False

        # Write opening element
        if kwargs:
            params = ' '.join('{}={}'.format(reserved(k), v.__repr__()) for k, v in kwargs.items())
            Element.Lines.append('{}<{} {}/>'.format(self.indent, self.__class__.__name__, params))
        else:
            Element.Lines.append('{}<{}/>'.format(self.indent, self.__class__.__name__))
    
    def __enter__(self):
        self._context_manager = True
        Element.Lines[-1] = Element.Lines[-1][:-2] + Element.Lines[-1][-1]  # Swap "/>" for ">"
        Element.Depth += 1
        return self

    def __exit__(self, *args):
        # Write text
        if Element.RawText:
            lines = len(Element.RawText)
            text = '<br/>'.join(Element.RawText)
            Element.RawText = []

            if lines > 1:
                with self.parent.p() as paragraph:
                    paragraph(text)
            else:
                self.write_text(text)

        # Write closing element
        Element.Depth -= 1
        Element.Lines.append('{}</{}>'.format(self.indent, self.__class__.__name__))
    
    def __call__(self, text):
        """Add text into the element."""
        Element.RawText.append(text)

        # Force the functions to correctly apply text
        if not self._context_manager:
            self.__enter__()
            self.__exit__(None, None, None)

    @classmethod
    def write_text(cls, text):
        indent = ' ' * (cls.IndentSpacing * Element.Depth)
        Element.Lines.append(indent + text.replace('<br/>', '\n{i}<br/>\n{i}'.format(i=indent)))


class WebPage(object):
    def __enter__(self):
        Element.Lines = []
        Element.Depth = 0
        Element.RawText = []
        return self

    def __exit__(self, *args):
        self.html = '\n'.join(Element.Lines)

    def __getattr__(self, attr):
        return type(attr, (Element,), {'parent': self})
    
    def __call__(self, text):
        Element.RawText.append(text)


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

    with WebPage() as w:
        with w.html(lang='en'):
            with w.head():
                w.title()('Python Flask Bucket List App')
                w.link(href='http://getbootstrap.com/dist/css/bootstrap.min.css', rel='stylesheet')
                w.link(href='http://getbootstrap.com/examples/jumbotron-narrow/jumbotron-narrow.css', rel='stylesheet')
            with w.body():
                with w.div(class_='container'):
                    with w.div(class_='header'):
                        with w.nav():
                            with w.ul(class_='nav nav-pills pull-right'):
                                for i, item in enumerate(('Home', 'Sign In', 'Sign Up')):
                                    if i:
                                        kwargs = {}
                                    else:
                                        kwargs = {'class_': 'active'}
                                    with w.li(role='presentation', **kwargs):
                                        w.a(href='#')(item)
                        w.h3(class_='text-muted')('Python Flask App')

    assert w.html == example.replace('"', "'")
