# -*- coding:utf-8 -*-
import re

# Query-string keys whose values are credentials and must never be logged.
_SECRET_PARAM_RE = re.compile(
	r'(?i)(\b(?:api[_-]?key|access[_-]?token|apikey|key|token)=)([^&\s]+)'
)


def mask_url(url):
	"""Return URL with any credential-bearing query parameters masked."""
	if not isinstance(url, str):
		return url
	return _SECRET_PARAM_RE.sub(r'\1***', url)


def mask_text(text):
	"""Mask credentials inside an arbitrary text blob (e.g. an Overpass query)."""
	return mask_url(text)
