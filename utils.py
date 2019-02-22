# -*- coding: utf-8 -*-
"""
url encode and decode
@author: yanyongyu
"""

__author__ = "yanyongyu"
__all__ = ["decode_uri_component", "encode_uri_component"]

from urllib import parse


def encode_uri_component(text):
    return parse.quote(text, safe='~()*!.\'')


def decode_uri_component(text):
    return parse.unquote(text)
