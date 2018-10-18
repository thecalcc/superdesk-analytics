# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2018 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

from superdesk.tests import TestCase

from analytics import init_app
from analytics.chart_config import ChartConfig


class ChartConfigTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None

        with self.app.app_context():
            init_app(self.app)

            self.app.data.insert('vocabularies', [{
                '_id': 'categories',
                'items': [
                    {'qcode': 'a', 'name': 'Advisories', 'is_active': True},
                    {'qcode': 'b', 'name': 'Basketball', 'is_active': True},
                    {'qcode': 'c', 'name': 'Cricket', 'is_active': True}
                ]
            }, {
                '_id': 'urgency',
                'items': [
                    {'qcode': 1, 'name': 1, 'is_active': True},
                    {'qcode': 2, 'name': 2, 'is_active': True},
                    {'qcode': 3, 'name': 3, 'is_active': True},
                    {'qcode': 4, 'name': 4, 'is_active': True},
                    {'qcode': 5, 'name': 5, 'is_active': True}
                ]
            }, {
                '_id': 'genre',
                'items': [
                    {'qcode': 'Article', 'name': 'Article (news)', 'is_active': True},
                    {'qcode': 'Sidebar', 'name': 'Sidebar', 'is_active': True},
                    {'qcode': 'Factbox', 'name': 'Factbox', 'is_active': True}
                ],
            }])

            self.app.data.insert('desks', [
                {'_id': 'desk1', 'name': 'Politic Desk'},
                {'_id': 'desk2', 'name': 'Sports Desk'},
                {'_id': 'desk3', 'name': 'System Desk'}
            ])

            self.app.data.insert('users', [
                {'_id': 'user1', 'display_name': 'first user'},
                {'_id': 'user2', 'display_name': 'second user'},
                {'_id': 'user3', 'display_name': 'last user'}
            ])

    @staticmethod
    def _gen_single_chart(chart_id, chart_type):
        chart = ChartConfig(chart_id, chart_type)
        chart.add_source('anpa_category.qcode', {'a': 3, 'b': 4, 'c': 1})
        return chart

    @staticmethod
    def _gen_stacked_chart(chart_id, chart_type):
        chart = ChartConfig(chart_id, chart_type)
        chart.add_source('anpa_category.qcode', {
            'a': {1: 1, 3: 1},
            'b': {1: 1, 3: 2},
            'c': {1: 2, 3: 1, 5: 1},
        })
        chart.add_source('urgency', {1: 4, 3: 4, 5: 1})
        return chart

    def test_generate_single_series(self):
        chart = self._gen_single_chart('cid', 'bar')
        chart.title = 'Charts'
        chart.subtitle = 'For Today'

        self.assertFalse(chart.is_multi_source())
        self.assertEqual(chart.gen_config(), {
            'id': 'cid',
            'type': 'bar',
            'chart': {
                'type': 'bar',
                'zoomType': 'y',
            },
            'title': {'text': 'Charts'},
            'subtitle': {'text': 'For Today'},
            'xAxis': {
                'title': {'text': 'Category'},
                'categories': ['Basketball', 'Advisories', 'Cricket'],
            },
            'yAxis': {
                'title': {'text': 'Published Stories'},
                'stackLabels': {'enabled': False},
                'allowDecimals': False,
            },
            'legend': {'enabled': False},
            'tooltip': {
                'headerFormat': '{point.x}: {point.y}',
                'pointFormat': '',
            },
            'plotOptions': {
                'bar': {
                    'colorByPoint': True,
                    'dataLabels': {'enabled': True},
                },
                'column': {
                    'colorByPoint': True,
                    'dataLabels': {'enabled': True},
                },
            },
            'series': [{
                'name': 'Published Stories',
                'data': [4, 3, 1],
            }],
            'credits': {'enabled': False},
        })

    def test_sort_single_series(self):
        chart = self._gen_single_chart('cid', 'bar')
        chart.sort_order = 'asc'

        config = chart.gen_config()
        self.assertEqual(config['xAxis'], {
            'title': {'text': 'Category'},
            'categories': ['Cricket', 'Advisories', 'Basketball'],
        })
        self.assertEqual(config['series'], [{
            'name': 'Published Stories',
            'data': [1, 3, 4]
        }])

        chart.sort_order = 'desc'
        config = chart.gen_config()
        self.assertEqual(config['xAxis'], {
            'title': {'text': 'Category'},
            'categories': ['Basketball', 'Advisories', 'Cricket'],
        })
        self.assertEqual(config['series'], [{
            'name': 'Published Stories',
            'data': [4, 3, 1]
        }])

    def test_generate_stacked_series(self):
        chart = self._gen_stacked_chart('cid', 'column')
        chart.title = 'Charts'
        chart.subtitle = 'For Today'

        self.assertTrue(chart.is_multi_source())
        self.assertEqual(chart.gen_config(), {
            'id': 'cid',
            'type': 'column',
            'chart': {
                'type': 'column',
                'zoomType': 'x',
            },
            'title': {'text': 'Charts'},
            'subtitle': {'text': 'For Today'},
            'xAxis': {
                'title': {'text': 'Category'},
                'categories': ['Cricket', 'Basketball', 'Advisories'],
            },
            'yAxis': {
                'title': {'text': 'Published Stories'},
                'stackLabels': {'enabled': True},
                'allowDecimals': False,
            },
            'legend': {
                'enabled': True,
                'title': {'text': 'Urgency'},
            },
            'tooltip': {
                'headerFormat': '{series.name}/{point.x}: {point.y}',
                'pointFormat': '',
            },
            'plotOptions': {
                'bar': {
                    'stacking': 'normal',
                    'colorByPoint': False,
                },
                'column': {
                    'stacking': 'normal',
                    'colorByPoint': False,
                },
            },
            'series': [{
                'name': '1',
                'data': [2, 1, 1],
            }, {
                'name': '3',
                'data': [1, 2, 1],
            }, {
                'name': '5',
                'data': [1, 0, 0]
            }],
            'credits': {'enabled': False},
        })

    def test_sort_stacked_series(self):
        chart = self._gen_stacked_chart('cid', 'bar')
        chart.sort_order = 'asc'

        config = chart.gen_config()
        self.assertEqual(config['xAxis'], {
            'title': {'text': 'Category'},
            'categories': ['Advisories', 'Basketball', 'Cricket'],
        })
        self.assertEqual(config['series'], [{
            'name': '1',
            'data': [1, 1, 2],
        }, {
            'name': '3',
            'data': [1, 2, 1],
        }, {
            'name': '5',
            'data': [0, 0, 1]
        }])

        chart.sort_order = 'desc'
        config = chart.gen_config()
        self.assertEqual(config['xAxis'], {
            'title': {'text': 'Category'},
            'categories': ['Cricket', 'Basketball', 'Advisories'],
        })
        self.assertEqual(config['series'], [{
            'name': '1',
            'data': [2, 1, 1],
        }, {
            'name': '3',
            'data': [1, 2, 1],
        }, {
            'name': '5',
            'data': [1, 0, 0]
        }])

    def test_generate_single_column_table(self):
        chart = self._gen_single_chart('tid', 'table')
        chart.title = 'Tables'
        chart.subtitle = 'For Today'

        self.assertFalse(chart.is_multi_source())
        self.assertEqual(chart.gen_config(), {
            'id': 'tid',
            'type': 'table',
            'chart': {'type': 'column'},
            'title': 'Tables',
            'subtitle': 'For Today',
            'xAxis': {
                'title': {'text': 'Category'},
                'categories': ['Basketball', 'Advisories', 'Cricket'],
            },
            'series': [{
                'name': 'Published Stories',
                'data': [4, 3, 1],
            }],
            'headers': ['Category', 'Published Stories'],
            'rows': [
                ['Basketball', 4],
                ['Advisories', 3],
                ['Cricket', 1]
            ],
            'credits': {'enabled': False}
        })

    def test_sort_single_column_table(self):
        chart = self._gen_single_chart('tid', 'table')
        chart.sort_order = 'asc'

        config = chart.gen_config()
        self.assertEqual(config['xAxis'], {
            'title': {'text': 'Category'},
            'categories': ['Cricket', 'Advisories', 'Basketball']
        })
        self.assertEqual(config['series'], [{
            'name': 'Published Stories',
            'data': [1, 3, 4]
        }])
        self.assertEqual(config['rows'], [
            ['Cricket', 1],
            ['Advisories', 3],
            ['Basketball', 4]
        ])

        chart.sort_order = 'desc'
        config = chart.gen_config()
        self.assertEqual(config['xAxis'], {
            'title': {'text': 'Category'},
            'categories': ['Basketball', 'Advisories', 'Cricket']
        })
        self.assertEqual(config['series'], [{
            'name': 'Published Stories',
            'data': [4, 3, 1]
        }])
        self.assertEqual(config['rows'], [
            ['Basketball', 4],
            ['Advisories', 3],
            ['Cricket', 1]
        ])

    def test_generate_multi_column_table(self):
        chart = self._gen_stacked_chart('tid', 'table')
        chart.title = 'Tables'
        chart.subtitle = 'For Today'

        self.assertTrue(chart.is_multi_source())
        self.assertEqual(chart.gen_config(), {
            'id': 'tid',
            'type': 'table',
            'chart': {'type': 'column'},
            'title': 'Tables',
            'subtitle': 'For Today',
            'xAxis': {
                'title': {'text': 'Category'},
                'categories': ['Cricket', 'Basketball', 'Advisories'],
            },
            'series': [{
                'name': '1',
                'data': [2, 1, 1],
            }, {
                'name': '3',
                'data': [1, 2, 1],
            }, {
                'name': '5',
                'data': [1, 0, 0],
            }],
            'headers': ['Category', '1', '3', '5', 'Total Stories'],
            'rows': [
                ['Cricket', 2, 1, 1, 4],
                ['Basketball', 1, 2, 0, 3],
                ['Advisories', 1, 1, 0, 2],
            ],
            'credits': {'enabled': False},
        })

    def test_sort_multi_column_table(self):
        chart = self._gen_stacked_chart('tid', 'table')
        chart.sort_order = 'asc'

        config = chart.gen_config()
        self.assertEqual(config['xAxis'], {
            'title': {'text': 'Category'},
            'categories': ['Advisories', 'Basketball', 'Cricket'],
        })
        self.assertEqual(config['series'], [{
            'name': '1',
            'data': [1, 1, 2],
        }, {
            'name': '3',
            'data': [1, 2, 1],
        }, {
            'name': '5',
            'data': [0, 0, 1],
        }])
        self.assertEqual(config['rows'], [
            ['Advisories', 1, 1, 0, 2],
            ['Basketball', 1, 2, 0, 3],
            ['Cricket', 2, 1, 1, 4],
        ])

        chart.sort_order = 'desc'
        config = chart.gen_config()
        self.assertEqual(config['xAxis'], {
            'title': {'text': 'Category'},
            'categories': ['Cricket', 'Basketball', 'Advisories'],
        })
        self.assertEqual(config['series'], [{
            'name': '1',
            'data': [2, 1, 1],
        }, {
            'name': '3',
            'data': [1, 2, 1],
        }, {
            'name': '5',
            'data': [1, 0, 0],
        }])
        self.assertEqual(config['rows'], [
            ['Cricket', 2, 1, 1, 4],
            ['Basketball', 1, 2, 0, 3],
            ['Advisories', 1, 1, 0, 2],
        ])

    def test_change_chart_functionality(self):
        chart = self._gen_single_chart('cid', 'bar')
        chart.title = 'Charts'
        chart.subtitle = 'For Today'

        self.assertFalse(chart.is_multi_source())

        def get_title():
            return '{} - Testing'.format(chart.title)

        def get_subtitle():
            return '{} - Test 2'.format(chart.subtitle)

        def gen_source_name(group):
            if group == 'anpa_category.qcode':
                return 'Category'
            elif group == 'genre.qcode':
                return 'Genre'
            elif group == 'source':
                return 'Source'
            elif group == 'urgency':
                return 'Urgency'
            return group

        def get_qcode_name(qcode):
            if qcode == 'a':
                return 'Advisories'
            elif qcode == 'b':
                return 'Basketball'
            elif qcode == 'c':
                return 'Cricket'
            return qcode

        def gen_source_titles(source_type, data_keys):
            return [get_qcode_name(qcode) for qcode in data_keys]

        chart.get_title = get_title
        chart.get_subtitle = get_subtitle
        chart.get_source_name = gen_source_name
        chart.get_source_titles = gen_source_titles

        config = chart.gen_config()
        self.assertEqual(config['title'], {'text': 'Charts - Testing'})
        self.assertEqual(config['subtitle'], {'text': 'For Today - Test 2'})
        self.assertEqual(config['xAxis'], {
            'title': {'text': 'Category'},
            'categories': ['Basketball', 'Advisories', 'Cricket']
        })

    def test_translate_anpa_category(self):
        chart = ChartConfig('catrgory', 'bar')
        chart.add_source('anpa_category.qcode', {'a': 3, 'b': 4, 'c': 1})

        self.assertEqual(chart.translations, {})

        chart.load_translations()
        self.assertEqual(chart.translations, {
            'anpa_category.qcode': {
                'title': 'Category',
                'names': {
                    'a': 'Advisories',
                    'b': 'Basketball',
                    'c': 'Cricket'
                }
            }
        })

        self.assertEqual(chart.get_x_axis_config(), {
            'title': {'text': 'Category'},
            'categories': ['Basketball', 'Advisories', 'Cricket']
        })

    def test_translate_urgency(self):
        chart = ChartConfig('urgency', 'bar')
        chart.add_source('urgency', {1: 4, 3: 4, 5: 1})

        self.assertEqual(chart.translations, {})

        chart.load_translations()
        self.assertEqual(chart.translations, {
            'urgency': {
                'title': 'Urgency',
                'names': {
                    1: 1,
                    2: 2,
                    3: 3,
                    4: 4,
                    5: 5
                }
            }
        })

        self.assertEqual(chart.get_x_axis_config(), {
            'title': {'text': 'Urgency'},
            'categories': [1, 3, 5]
        })

    def test_translate_genre(self):
        chart = ChartConfig('genre', 'bar')
        chart.add_source('genre.qcode', {'Article': 4, 'Sidebar': 5, 'Factbox': 1})

        self.assertEqual(chart.translations, {})

        chart.load_translations()
        self.assertEqual(chart.translations, {
            'genre.qcode': {
                'title': 'Genre',
                'names': {
                    'Article': 'Article (news)',
                    'Sidebar': 'Sidebar',
                    'Factbox': 'Factbox'
                }
            }
        })

        self.assertEqual(chart.get_x_axis_config(), {
            'title': {'text': 'Genre'},
            'categories': ['Sidebar', 'Article (news)', 'Factbox']
        })

    def test_translate_desk(self):
        chart = ChartConfig('desk', 'bar')
        chart.add_source('task.desk', {'desk1': 4, 'desk2': 5, 'desk3': 1})

        self.assertEqual(chart.translations, {})

        chart.load_translations()
        self.assertEqual(chart.translations, {
            'task.desk': {
                'title': 'Desk',
                'names': {
                    'desk1': 'Politic Desk',
                    'desk2': 'Sports Desk',
                    'desk3': 'System Desk'
                }
            }
        })

        self.assertEqual(chart.get_x_axis_config(), {
            'title': {'text': 'Desk'},
            'categories': ['Sports Desk', 'Politic Desk', 'System Desk']
        })

    def test_translate_user(self):
        chart = ChartConfig('user', 'bar')
        chart.add_source('task.user', {'user1': 3, 'user2': 4, 'user3': 5})

        self.assertEqual(chart.translations, {})

        chart.load_translations()
        self.assertEqual(chart.translations, {
            'task.user': {
                'title': 'User',
                'names': {
                    'user1': 'first user',
                    'user2': 'second user',
                    'user3': 'last user'
                }
            }
        })

        self.assertEqual(chart.get_x_axis_config(), {
            'title': {'text': 'User'},
            'categories': ['last user', 'second user', 'first user']
        })

    def test_translate_state(self):
        chart = ChartConfig('state', 'bar')
        chart.add_source('state', {'published': 3, 'killed': 1, 'updated': 5})

        self.assertEqual(chart.translations, {})

        chart.load_translations()
        self.assertEqual(chart.translations, {
            'state': {
                'title': 'State',
                'names': {
                    'published': 'Published',
                    'killed': 'Killed',
                    'corrected': 'Corrected',
                    'updated': 'Updated',
                }
            }
        })

        self.assertEqual(chart.get_x_axis_config(), {
            'title': {'text': 'State'},
            'categories': ['Updated', 'Published', 'Killed']
        })

    def test_translate_source(self):
        chart = ChartConfig('source', 'bar')
        chart.add_source('source', {'aap': 3, 'ftp': 1, 'ap': 5})

        self.assertEqual(chart.translations, {})

        chart.load_translations()
        self.assertEqual(chart.translations, {
            'source': {'title': 'Source'}
        })

        self.assertEqual(chart.get_x_axis_config(), {
            'title': {'text': 'Source'},
            'categories': ['ap', 'aap', 'ftp']
        })
