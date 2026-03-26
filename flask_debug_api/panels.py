import jinja2
import re

from flask import current_app, url_for
from markupsafe import Markup
from flask_debugtoolbar.panels import DebugPanel

# Compatibility shim for parse_rule which was removed from Werkzeug
def parse_rule(rule_string):
    '''
    Replace the removed parse_rule function from werkzeug.routing
    Returns tuples of (converter, arguments, variable)
    '''
    parts = []
    # Pattern to match URL variables like <id> or <int:post_id>
    pattern = r'<(?:([^>:]+):)?([^>]+)>'
    
    pos = 0
    for match in re.finditer(pattern, rule_string):
        # Add static part before the variable
        if match.start() > pos:
            static_text = rule_string[pos:match.start()]
            if static_text:
                parts.append((None, None, static_text))
        
        # Add variable part
        converter = match.group(1)  # converter type (e.g., 'int'), might be None
        variable = match.group(2)   # variable name
        parts.append((converter, None, variable))
        pos = match.end()
    
    # Add remaining static part after last variable
    if pos < len(rule_string):
        static_text = rule_string[pos:]
        if static_text:
            parts.append((None, None, static_text))
    
    return parts

template_loader = jinja2.PrefixLoader({
    'debug-api': jinja2.PackageLoader(__name__, 'templates/debug-api')
})


def _prefix():
    return current_app.config.get('DEBUG_API_PREFIX', '')


class BrowseAPIPanel(DebugPanel):
    """
    Panel that displays the API browser
    """
    name = 'DebugAPI'
    has_content = True

    def __init__(self, jinja_env, context={}):
        DebugPanel.__init__(self, jinja_env, context=context)
        self.jinja_env.loader = jinja2.ChoiceLoader([
            self.jinja_env.loader, template_loader])
        self.variables = {}

    def nav_title(self):
        return 'API Browse'

    def title(self):
        return 'API Browse'

    def url(self):
        return ''

    def nav_subtitle(self):
        count = len(self.routes)
        return '%s %s' % (count, 'route' if count == 1 else 'routes')

    def process_request(self, request):
        rs = current_app.url_map.iter_rules()
        self.routes = [r for r in rs if r.rule.startswith(_prefix())]
        for r in self.routes:
            self.variables[r.rule] = self.url_builder(r)

    def content(self):
        return self.render('debug-api/routes.html', {
            'routes': self.routes,
            'prefix': _prefix(),
            'url_for': url_for,
            'variables': self.variables
        })

    def url_builder(self, route):
        parts = []
        for (converter, arguments, variable) in parse_rule(route.rule):
            parts.append({'variable': converter is not None, 'text': variable})

        content = self.render('debug-api/url-builder.html', {
            'route': route,
            'parts': parts,
            'url_for': url_for
        })
        return Markup(content)
