import os
from textwrap import dedent

from django.core import management
from django.test import TestCase

from puente.commands import extract_command
from puente import settings as puente_settings


class TestManageExtract(TestCase):
    def test_help(self):
        try:
            management.call_command('extract', '--help')
        except SystemExit:
            # Calling --help causes it to call sys.exit(0) which
            # will otherwise exit.
            pass


def nix_header(pot_file):
    """Nix the POT file header since it changes and we don't care"""
    return pot_file[pot_file.find('\n\n')+2:]


class TestExtractCommand:
    def test_basic_extraction(self, tmpdir):
        # Create files to extract from
        tmpdir.join('foo.py').write(dedent("""\
        _('python string')
        """))
        tmpdir.join('foo.html').write(dedent("""\
        <html>
        {{ _('html string') }}
        {% trans %}
            html trans
            block
        {% endtrans %}
        </html>
        """))

        # Extract
        extract_command(
            domain='all',
            outputdir=str(tmpdir),
            domain_methods={
                'django': [
                    ('*.py', 'puente.extract.extract_python'),
                    ('*.html', 'puente.extract.extract_jinja2')
                ]
            },
            standalone_domains=puente_settings.STANDALONE_DOMAINS,
            keywords=puente_settings.KEYWORDS,
            comment_tags=puente_settings.COMMENT_TAGS,
            basedir=str(tmpdir)
        )

        # Verify contents
        assert os.path.exists(str(tmpdir.join('django.pot')))
        pot_file = nix_header(tmpdir.join('django.pot').read())
        assert (
            pot_file ==
            dedent("""\
            #: foo.html:2
            msgid "html string"
            msgstr ""

            #: foo.html:3
            msgid "html trans block"
            msgstr ""

            #: foo.py:1
            msgid "python string"
            msgstr ""
            """)
        )

    def test_whitespace_collapsing(self, tmpdir):
        # We collapse whitespace in Jinja2 trans tags and that's it.
        tmpdir.join('foo.py').write(dedent("""\
        _("  gettext1  test  ")
        """))
        tmpdir.join('foo.html').write(dedent("""\
        {{ _("  gettext2  test  ") }}
        """))
        tmpdir.join('foo2.html').write(dedent("""\
        {% trans %}
            trans
            tag
            test
        {% endtrans %}
        """))

        # Extract
        extract_command(
            domain='all',
            outputdir=str(tmpdir),
            domain_methods={
                'django': [
                    ('*.py', 'puente.extract.extract_python'),
                    ('*.html', 'puente.extract.extract_jinja2')
                ]
            },
            standalone_domains=puente_settings.STANDALONE_DOMAINS,
            keywords=puente_settings.KEYWORDS,
            comment_tags=puente_settings.COMMENT_TAGS,
            basedir=str(tmpdir)
        )

        # Verify contents
        assert os.path.exists(str(tmpdir.join('django.pot')))
        pot_file = nix_header(tmpdir.join('django.pot').read())
        assert (
            pot_file ==
            dedent("""\
            #: foo.html:1
            msgid "  gettext2  test  "
            msgstr ""

            #: foo.py:1
            msgid "  gettext1  test  "
            msgstr ""

            #: foo2.html:1
            msgid "trans tag test"
            msgstr ""
            """)
        )

    def test_context(self, tmpdir):
        # Test context
        tmpdir.join('foo.py').write(dedent("""\
        pgettext("context", "string")
        """))
        tmpdir.join('foo.html').write(dedent("""\
        {{ _("  gettext2  test  ", "context") }}
        """))

        # Extract
        extract_command(
            domain='all',
            outputdir=str(tmpdir),
            domain_methods={
                'django': [
                    ('*.py', 'puente.extract.extract_python'),
                    ('*.html', 'puente.extract.extract_jinja2')
                ]
            },
            standalone_domains=puente_settings.STANDALONE_DOMAINS,
            keywords=puente_settings.KEYWORDS,
            comment_tags=puente_settings.COMMENT_TAGS,
            basedir=str(tmpdir)
        )

        # Verify contents
        assert os.path.exists(str(tmpdir.join('django.pot')))
        pot_file = nix_header(tmpdir.join('django.pot').read())
        assert (
            pot_file ==
            dedent("""\
            #: foo.html:1
            msgid "  gettext2  test  "
            msgstr ""

            #: foo.py:1
            msgctxt "context"
            msgid "string"
            msgstr ""
            """)
        )