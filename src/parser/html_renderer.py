
class HtmlRendererMixin:
    def render_blue_elem(self, elem):
        return f'<blue hello>{self.render_children(elem)}</blue>'