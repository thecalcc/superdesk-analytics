# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2018 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

from superdesk.resource import Resource

from analytics.base_report import BaseReportService
from analytics.chart_config import ChartConfig

from datetime import datetime, timedelta


class PublishingPerformanceReportResource(Resource):
    """Publishing Performance Report schema
    """

    item_methods = ['GET']
    resource_methods = ['GET']
    privileges = {'GET': 'publishing_performance_report'}


class PublishingPerformanceReportService(BaseReportService):
    aggregations = {
        'source': {
            'terms': {
                'field': 'source',
                'size': 0,
            }
        }
    }

    @staticmethod
    def _get_aggregation_query(agg):
        include = agg.get('filter') or 'all'

        query = {
            'terms': {
                'field': agg.get('field'),
                'size': agg.get('size') or 0
            },
            'aggs': {
                'no_rewrite_of': {
                    'filter': {
                        'not': {
                            'filter': {
                                'exists': {
                                    'field': 'rewrite_of'
                                }
                            }
                        }
                    },
                    'aggs': {
                        'state': {
                            'terms': {
                                'field': 'state'
                            }
                        }
                    }
                },
                'rewrite_of': {
                    'filter': {
                        'exists': {
                            'field': 'rewrite_of'
                        }
                    },
                    'aggs': {
                        'state': {
                            'terms': {
                                'field': 'state'
                            }
                        }
                    }
                }
            }
        }

        if include != 'all':
            query['terms']['include'] = include
            query['terms']['min_doc_count'] = 0

        return query

    def run_query(self, request, params):
        aggs = params.pop('aggs', None)

        if not aggs or not (aggs.get('group') or {}).get('field'):
            self.aggregations = PublishingPerformanceReportService.aggregations
            return super().run_query(request, params)

        self.aggregations = {
            'parent': self._get_aggregation_query(aggs['group'])
        }

        docs = super().run_query(request, params)

        return docs

    def generate_report(self, docs, args):
        """Returns the publishing statistics

        :param docs: document used for generating the statistics
        :return dict: report
        """
        agg_buckets = self.get_aggregation_buckets(getattr(docs, 'hits'))

        report = {
            'groups': {},
            'subgroups': {
                'killed': 0,
                'corrected': 0,
                'updated': 0,
                'published': 0
            }
        }

        for parent in agg_buckets.get('parent') or []:
            parent_key = parent.get('key')

            if not parent_key:
                continue

            report['groups'][parent_key] = {
                'killed': 0,
                'corrected': 0,
                'updated': 0,
                'published': 0,
            }

            no_rewrite_of = (parent.get('no_rewrite_of') or {}).get('state') or {}
            rewrite_of = (parent.get('rewrite_of') or {}).get('state') or {}

            for child in no_rewrite_of.get('buckets') or []:
                state_key = child.get('key')

                if not state_key:
                    continue

                doc_count = child.get('doc_count') or 0

                if state_key == 'published':
                    report['groups'][parent_key]['published'] += doc_count
                    report['subgroups']['published'] += doc_count
                elif state_key == 'killed':
                    report['groups'][parent_key]['killed'] += doc_count
                    report['subgroups']['killed'] += doc_count

            for child in rewrite_of.get('buckets') or []:
                state_key = child.get('key')

                if not state_key:
                    continue

                doc_count = child.get('doc_count') or 0

                if state_key == 'corrected':
                    report['groups'][parent_key]['corrected'] += doc_count
                    report['subgroups']['corrected'] += doc_count
                elif state_key == 'published':
                    report['groups'][parent_key]['updated'] += doc_count
                    report['subgroups']['updated'] += doc_count

        return report

    def generate_highcharts_config(self, docs, args):
        params = args.get('params') or {}
        aggs = args.get('aggs') or {}
        group = aggs.get('group') or {}
        subgroup = aggs.get('subgroup') or {}

        chart = params.get('chart') or {}
        chart_type = chart.get('type') or 'bar'

        report = self.generate_report(docs, args)

        chart_config = ChartConfig('content_publishing', chart_type)

        group_keys = list(report['groups'].keys())
        if len(group_keys) == 1 and report.get('subgroups'):
            chart_config.add_source(
                subgroup.get('field'),
                report['subgroups']
            )
            chart_config.load_translations(group.get('field'))
        else:
            chart_config.add_source(group.get('field'), report.get('groups'))
            if report.get('subgroups'):
                chart_config.add_source(subgroup.get('field'), report['subgroups'])

        def gen_title():
            if chart.get('title'):
                return chart['title']

            group_type = group.get('field')
            group_title = chart_config.get_source_name(group_type)

            if len(group_keys) == 1 and report.get('subgroups'):
                data_name = chart_config.get_source_title(
                    group_type,
                    group_keys[0]
                )

                return 'Published Stories for {}: {}'.format(
                    group_title,
                    data_name
                )

            return 'Published Stories per {}'.format(group_title)

        def gen_subtitle():
            if chart.get('subtitle'):
                return chart['subtitle']

            dates = params.get('dates') or {}
            date_filter = dates.get('filter')

            if date_filter == 'range':
                start = datetime.strptime(dates.get('start'), '%Y-%m-%d')
                end = datetime.strptime(dates.get('end'), '%Y-%m-%d')

                return '{} - {}'.format(
                    start.strftime('%B %-d, %Y'),
                    end.strftime('%B %-d, %Y')
                )
            elif date_filter == 'yesterday':
                return (datetime.today() - timedelta(days=1))\
                    .strftime('%A %-d %B %Y')
            elif date_filter == 'last_week':
                week = datetime.today() - timedelta(weeks=1)
                start = week - timedelta(days=week.weekday() + 1)
                end = start + timedelta(days=6)

                return '{} - {}'.format(
                    start.strftime('%B %-d, %Y'),
                    end.strftime('%B %-d, %Y')
                )
            elif date_filter == 'last_month':
                first = datetime.today().replace(day=1)
                month = first - timedelta(days=1)

                return month.strftime('%B %Y')

            return None

        chart_config.get_title = gen_title
        chart_config.get_subtitle = gen_subtitle
        chart_config.sort_order = chart.get('sort_order') or 'desc'

        report['highcharts'] = [chart_config.gen_config()]

        return report
