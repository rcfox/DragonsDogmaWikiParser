import os
import re
import html
import html.parser

from collections import defaultdict

WEAPON_CATEGORIES = {
    'Swords',
    'Maces',
    'Longswords',
    'Warhammers',
    'Daggers',
    'Staves',
    'Archistaves',
    'Longbows',
    'Magick Bows',
    'Bows',
    'Shields',
    'Magick Shields'
}

ARMOR_CATEGORIES = {
    'Head Armor',
    'Leg Clothing',
    'Leg Armor',
    'Chest Clothing',
    'Torso Armor',
    'Arms Armor',
    'Cloaks',
}

CATEGORIES = WEAPON_CATEGORIES.union(ARMOR_CATEGORIES)

LEVEL_NAME = [
    '0 Stars',
    '1 Star',
    '2 Stars',
    '3 Stars',
    'Dragonforged',
    'Silver Rarified',
    'Gold Rarified'
]

def icon_tag(element, image):
    return element, '[[File:{image}|32px|link={element}|{element}]]'.format(element=element,
                                                                            image=image)
ELEMENT_IMAGES = {
    'Fire': 'FIRE BASED.png',
    'Ice': 'ICE BASED.png',
    'Lightning': 'LIGHTNING BASED.png',
    'Holy': 'HOLY BASED.png',
    'Dark': 'DARK BASED.png',
    'Darkness': 'DARK BASED.png',

    'Burning': 'Fire.png',
    'Tarring': 'Tarred.png',
    'Tarred': 'Tarred.png',
    'Drenched': 'DrenchedWater.png',
    'Frozen': 'Frozen.png',
    'Thundershock': 'LIGHTNING BASED.png',
    'Shock': 'LIGHTNING BASED.png',
    'Blind': 'Blindness.png',
    'Blindness': 'Blindness.png',
    'Curse': 'Curse.png',
    'Cursed': 'Curse.png',
    'Lowered Defense': 'DefenseLowered.png',
    'Lowered Magick': 'MagickLowered.png',
    'Lowered Magick Defense': 'MagickDefenseLowered.png',
    'Lowered Strength': 'StrengthLowered.png',
    'Petrification': 'Petrification.png',
    'Poison': 'Poison.png',
    'Possession': 'Possession.png',
    'Silence': 'Silence.png',
    'Skill Stifling': 'SkillStifling.png',
    'Sleep': 'Sleep.png',
    'Torpor': 'Torpor.png'
}
ELEMENT_ICONS = dict(icon_tag(element, filename) for element, filename in ELEMENT_IMAGES.items())


def strip_html(html_data):
    '''
    Strip out any HTML tags, leaving only the data inside (or outside) of the tags.
    "<b>foo</b>" -> "foo"
    '''
    text = []
    class HTMLStripper(html.parser.HTMLParser):
        ignore = False
        def handle_starttag(self, tag, attrs):
            # Ignore the contents of <ref> tags.
            if tag == 'ref':
                self.ignore = True

        def handle_endtag(self, tag):
            if tag == 'ref':
                self.ignore = False

        def handle_data(self, data):
            if not self.ignore:
                text.append(data.strip())

    stripper = HTMLStripper()
    stripper.feed(html_data)
    return ' '.join(text)


def red_text(text):
    return '<span style="color: #f00">{text}</span>'.format(text=text)


def parse_value(key, value):
    text = strip_html(html.unescape(value)).replace('\n', '').replace('&nbsp;', ' ')
    if key.startswith('element') or key.startswith('debil'):
        element_stats = {}
        elements = text.split('[[')[1:]
        for element in elements:
            key, value = re.sub(r'\|.*?\]\]', ']]', element).split(']]')
            value = value.strip()
            if value.startswith('-'):
                value = red_text(value)
            element_stats[key.strip()] = value
        return element_stats
    else:
        text = text.strip()
        if len(text) > 1 and text.startswith('-'):
            text = red_text(text)

    return text


def parse_templates(text):
    '''
    Parse a page for MediaWiki templates to get their names, and parameters as dictionaries.
    ie: {{MyTemplate|foo=1|bar=2}} -> ('MyTemplate', {'foo': 1, 'bar': 2})
    Parameter values might have wiki links: [[Wiki URL|text description]]
    '''
    templates = []
    brace_count = 0
    bracket_count = 0
    last_index = 0
    parameters = None
    template_name = None
    for index, character in enumerate(text):
        if character == '{':
            brace_count += 1
            if brace_count == 2:
                last_index = index + 1
                parameters = {}

        elif character == '[':
            bracket_count += 1

        elif character == ']':
            bracket_count -= 1

        elif character == '|' or character == '}':

            if brace_count > 1 and bracket_count == 0:
                param = text[last_index : index].strip()
                last_index = index + 1
                if '=' in param:
                    key, value = re.split(r'\s*=\s*', param, 1)
                    parameters[key] = parse_value(key, value)
                else:
                    template_name = param.strip()

            if character == '}':
                brace_count -= 1
                last_index = index
                if brace_count == 0 and text[index-1] == '}' and template_name is not None:
                    templates.append((template_name, parameters))
                    template_name = None
                    parameters = None

    return dict(templates)


def parse_page_text(filename):
    with open(filename) as f:
        text = f.read()
        title = re.search(r'<title>(.*?)</title>', text).group(1)
        # Ignore sets for now
        if ' set' in title.lower() or 'category' in title.lower():
            return None, title, {}

        templates = parse_templates(text)
        item_type = None
        for template in templates.values():
            if 'type' in template:
                # Sort categories by string length so that we process 'Magick Bow' before 'Bow'.
                for category in sorted(CATEGORIES, key=len, reverse=True):
                    if category in template['type']:
                        item_type = category
                        break
    return item_type, title, templates


def compile_weapon(name, stats):
    levelless_stats = {
        'name': "'''[[%s]]'''" % name,
        'bludgeon': stats['bludg'],
        'slash': stats['slash'],
        'element': stats['element']
    }
    keys = ['strength', 'magick', 'stagger', 'knockdown', 'debil', 'req', 'weight']
    return compile_item(name, stats, levelless_stats, keys)


def compile_armor(name, stats):
    levelless_stats = {
        'name': "'''[[%s]]'''" % name,
        'bonus': stats.get('bonus', '')
    }
    keys = ['def', 'mdef', 'pierce', 'strike', 'element',
            'stagger', 'knockdown', 'debil', 'req', 'weight']
    return compile_item(name, stats, levelless_stats, keys)


def compile_item(name, stats, levelless_stats, keys):
    stats_by_level = []
    for i in range(7):
        stats_by_level.append({**levelless_stats, **{key: stats.get(key + str(i), '') for key in keys}})
    return {'name': name, 'stats': stats_by_level}


def build_weapon_category_table(items):
    # Key -> Rendered Text, in the order the columns will appear in the table.
    columns = [('name', 'Name'), ('strength', 'Strength'),
               ('magick', 'Magick'), ('slash', 'Slash Strength'),
               ('bludgeon', 'Bludgeon Strength'), ('stagger', 'Stagger Power'),
               ('knockdown', 'Knockdown Power'), ('element', 'Element'),
               ('debil', 'Debilitations'), ('weight', 'Weight')]
    # Weapons in each table are ordered by the gold-rarified strength+magick.
    items.sort(key=lambda item: int(item['stats'][-1]['strength'].replace('-', '0')) + int(item['stats'][-1]['magick'].replace('-', '0')), reverse=True)
    return build_tables(items, columns)


def build_armor_category_table(items):
    # Key -> Rendered Text, in the order the columns will appear in the table.
    columns = [('name', 'Name<br/><br/>'), ('def', 'Defense<br/><br/>'),
               ('mdef', 'Magick<br/>Defense<br/>'), ('pierce', 'Piercing<br/>Resist<br/>'),
               ('strike', 'Striking<br/>Resist<br/>'), ('stagger', 'Stagger<br/>Resist<br/>'),
               ('knockdown', 'Knockdown<br/>Resist<br/>'), ('element', 'Elemental<br/>Resist<br/>'),
               ('debil', 'Debilitation<br/>Resist<br/>'), ('weight', 'Weight<br/><br/>'),
               ('bonus', 'Bonus<br/><br/>')]
    # Armor in each table are ordered by the gold-rarified defense.
    items.sort(key=lambda item: int(item['stats'][-1]['def']), reverse=True)
    return build_tables(items, columns)


def build_tables(items, columns):
    '''
    Generate a MediaWiki table for each item level, split into tabs.
    '''
    tables = []
    for level in range(7):
        tables.append(build_table(columns, [item['stats'][level] for item in items]))
    tabs = []
    result = ['<!-- This markup was autogenerated by the scripts found here: https://github.com/rcfox/DragonsDogmaWikiParser -->',
              '<tabber>']
    for level in range(0,7):
        tabs.append('%s=%s' % (LEVEL_NAME[level], tables[level]))
    result.append('|-|'.join(tabs))
    result.append('</tabber>')
    result.append('<!-- End of autogenerated markup. -->')
    return '\n'.join(result)


def build_table(key_mapping, rows):
    table = ['{| class="wikitable-sortable sortable" style="border-collapse:collapse; border:1px solid darkslategray; font-size:85%; text-align:center;" cellpadding="3" border="1"']
    header_sep = '\n! class="txtbg1" style="text-align: center;" | '
    header_row = header_sep + header_sep.join(text for key, text in key_mapping)
    table.append(header_row)

    cell_sep = '| '
    row_sep = '\n|-\n'

    for row in rows:
        row_data = []
        for key, text in key_mapping:
            comment = ' <!-- %s -->' % text.replace('<br/>', ' ').strip()
            if isinstance(row[key], dict):
                cell_data = build_element_table(row[key])
            else:
                cell_data = row[key]
            row_data.append(cell_sep + cell_data + comment)
        table.append(row_sep + '\n'.join(row_data))

    table.append('\n|}')
    return '\n'.join(table)


def build_element_table(element):
    rows = []
    for key, value in element.items():
        rows.append('\n|-\n ! %s || %s' % (ELEMENT_ICONS[key], value))
    return '\n{| ' + ' '.join(rows) + ' \n|}'


def compile_all_data():
    item_stats = {}
    item_categories = defaultdict(list)
    category_items = defaultdict(list)
    for dirpath, _, filenames in os.walk('cache'):
        for filename in filenames:
            category, name, templates = parse_page_text(os.path.join(dirpath, filename))
            item_stats[name] = templates
            item_categories[category].append(name)

    for category, names in item_categories.items():
        for name in names:
            for template_name, stats in item_stats[name].items():
                # There's a bunch of templates that hold stats, but they're all something like
                # DDArmorStat or DDWeaponStat.
                if 'stat' in template_name.lower():
                    if category in WEAPON_CATEGORIES:
                        category_items[category].append(compile_weapon(name, stats))
                    elif category in ARMOR_CATEGORIES:
                        category_items[category].append(compile_armor(name, stats))
    return category_items


if __name__ == '__main__':
    import sys
    category = ' '.join(sys.argv[1:]).strip()
    if category not in CATEGORIES:
        print('"%s" category not recognized. Use one of:\n  %s' % (category, '\n  '.join(sorted(CATEGORIES))))
        exit(1)
    else:
        category_items = compile_all_data()
        if category in WEAPON_CATEGORIES:
            print(build_weapon_category_table(category_items[category]))
        else:
            print(build_armor_category_table(category_items[category]))
