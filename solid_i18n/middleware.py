from django.conf import settings
from django.core.urlresolvers import get_resolver
from django.http import HttpResponseRedirect
from django.utils.cache import patch_vary_headers
from django.utils import translation as trans
from urlresolvers import SolidLocaleRegexURLResolver
from django.middleware.locale import LocaleMiddleware


class SolidLocaleMiddleware(LocaleMiddleware):
    """
    Request without language prefix will use default language.
    Or, if settings.SOLID_I18N_USE_REDIRECTS is True, try to discover language.
    If language is not equal to default language, redirect to discovered
    language.

    If request contains language prefix, this language will be used immediately.
    In that case settings.SOLID_I18N_USE_REDIRECTS doesn't make sense.

    Default language is set in settings.LANGUAGE_CODE.
    """
    @property
    def use_redirects(self):
        return getattr(settings, 'SOLID_I18N_USE_REDIRECTS', False)

    @property
    def default_lang(self):
        return settings.LANGUAGE_CODE

    def process_request(self, request):
        check_path = self.is_language_prefix_patterns_used()
        if check_path and not self.use_redirects:
            language = trans.get_language_from_path(request.path_info)
            language = language or self.default_lang
        else:
            language = trans.get_language_from_request(request, check_path)
        trans.activate(language)
        request.LANGUAGE_CODE = trans.get_language()

    def process_response(self, request, response):
        language = trans.get_language()
        if self.use_redirects:
            rr_response = super(SolidLocaleMiddleware, self).process_response(request, response)
            if rr_response and not(
                    isinstance(rr_response, HttpResponseRedirect)
                    and language == self.default_lang):
                return rr_response
        trans.deactivate()

        patch_vary_headers(response, ('Accept-Language',))
        if 'Content-Language' not in response:
            response['Content-Language'] = language
        return response

    def is_language_prefix_patterns_used(self):
        """
        Returns `True` if the `SolidLocaleRegexURLResolver` is used
        at root level of the urlpatterns, else it returns `False`.
        """
        for url_pattern in get_resolver(None).url_patterns:
            if isinstance(url_pattern, SolidLocaleRegexURLResolver):
                return True
        return False
