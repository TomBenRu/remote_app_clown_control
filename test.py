from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout

from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase, MDTabsLabel, MDTabs
from kivymd.icon_definitions import md_icons

KV = '''
BoxLayout:
    orientation: "vertical"

    MDTopAppBar:
        title: "Example Tabs"

    MDTabs:
        id: android_tabs
        anchor_y: "bottom"
        on_tab_switch: app.on_tab_switch(*args)


<Tab>:
    MDLabel:
        id: tab_label
        user_font_size: "48sp"
        pos_hint: {"center_x": .5, "center_y": .5}
'''


class Tab(FloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''


class Example(MDApp):
    departments = ["Tokyo", "New York", "Mexico City"]

    def build(self):
        return Builder.load_string(KV)

    def on_start(self):
        for name_tab in self.departments:
            self.root.ids.android_tabs.add_widget(Tab(tab_label_text=name_tab))

    def on_tab_switch(self, instance_tabs: MDTabs, instance_tab, instance_tab_label: MDTabsLabel, tab_text, *args):
        '''Called when switching tabs.

        :type instance_tabs: <kivymd.uix.tab.MDTabs object>;
        :param instance_tab: <__main__.Tab object>;
        :param instance_tab_label: <kivymd.uix.tab.MDTabsLabel object>;
        :param tab_text: text or name icon of tab;
        '''
        print(instance_tabs, instance_tab, instance_tab_label.text, tab_text)
        instance_tab.ids.tab_label.text = instance_tab_label.text


Example().run()