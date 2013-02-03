#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2011, Scott Burns
All rights reserved.
"""

import requests
import json


class RCAPIError(Exception):
    """ Errors corresponding to a misuse of the REDCap API """
    pass


class RCRequest(object):
    """Private class wrapping the REDCap API

    see https://redcap.vanderbilt.edu/api/help/

    Decodes response from redcap and returns it.

    Users shouldn't really need to use this, the Project class will use this.
    """

    def __init__(self, url, payload, qtype):
        """Constructor

        Parameters
        ----------
        url: str
            REDCap API URL
        payload: dict
            key,values corresponding to the REDCap API
        qtype: 'imp_record' | 'exp_record' | 'metadata'
            Used to validate payload contents against API
        """
        self.url = url
        self.payload = payload
        self.type = qtype
        if qtype:
            self.validate_pl()
        fmt_key = 'returnFormat' if 'returnFormat' in payload else 'format'
        self.fmt = payload[fmt_key]

    def validate_pl(self):
        """Check that at least required params exist

        """
        required = ['token', 'content']
        if self.type == 'exp_record':
            extra = ['type', 'format']
            req_content = 'record'
            err_msg = 'Exporting record but content is not record'
        if self.type == 'imp_record':
            extra = ['type', 'overwriteBehavior', 'data', 'format']
            req_content = 'record'
            err_msg = 'Importing record but content is not record'
        if self.type == 'metadata':
            extra = ['format']
            req_content = 'metadata'
            err_msg = 'Requesting metadata but content != metadata'
        if self.type == 'exp_file':
            extra = ['action', 'record', 'field']
            req_content = 'file'
            err_msg = 'Exporting file but content is not file'
        if self.type == 'imp_file':
            extra = ['action', 'record', 'field']
            req_content = 'file'
            err_msg = 'Importing file but content is not file'
        if self.type == 'exp_event':
            extra = ['format']
            req_content = 'event'
            err_msg = 'Exporting events but content is not event'
        if self.type == 'exp_arm':
            extra = ['format']
            req_content = 'arm'
            err_msg = 'Exporting arms but content is not arm'
        if self.type == 'exp_fem':
            extra = ['format']
            req_content = 'formEventMapping'
            err_msg = 'Exporting form-event mappings but content is not ' + \
                    'formEventMapping'
        if self.type == 'exp_user':
            extra = ['format']
            req_content = 'user'
            err_msg = 'Exporting users but content is not user'
        required.extend(extra)
        required = set(required)
        pl_keys = set(self.payload.keys())
        # if req is not subset of payload keys, this call is wrong
        if not set(required) <= pl_keys:
            #what is not in pl_keys?
            not_pre = required - pl_keys
            raise RCAPIError("Required keys: %s" % ', '.join(not_pre))
        # Check content, raise with err_msg if not good
        try:
            if self.payload['content'] != req_content:
                raise RCAPIError(err_msg)
        except KeyError:
            raise RCAPIError('content not in payload')

    def execute(self, **kwargs):
        """Execute the API request and return data

        Parameters
        ----------
        kwargs: passed to requests.post()

        Returns
        -------
        Return data object from JSON decoding process if format=='json',
        else return raw string (ie format=='csv'|'xml')
        """
        header = {'Content-Type': 'application/x-www-form-urlencoded'}
        r = requests.post(self.url, verify=False, data=self.payload, headers=header,
            **kwargs)
        if self.type != 'exp_file':
            if self.fmt == 'json':
                try:
                    # REDCap likes to send bad json
                    content = json.loads(r.text, strict=False)
                except ValueError as e:
                    if self.type == 'imp_file':
                        # no response for successful file imports
                        content = {}
                    else:
                        raise ValueError(e)
            else:
                content = r.text
        else:
            # File exports need to return non-unicoded content

            # For file exports, file content comes where error
            # messages usually would be. Raising for non-200 responses
            # is the only way to signal that bad things happened.
            r.raise_for_status()

            content = r.content
        return content, r.headers
