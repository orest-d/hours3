from lqreports.constants import LinkType
from lqreports.util import dataurl, mimetype_from_extension
from lqreports.resource import resources_path
import pandas as pd
import numpy as np
from io import BytesIO


class RenderContext(object):
    def __init__(self, link_type=LinkType.LINK):
        self.link_type = link_type


class Register(dict):
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self[name] = value


class Renderable(object):
    def render(self, render_context=None):
        return ""


class Segment(Renderable):
    prefix = ""
    suffix = ""
    separator = ""

    def __init__(self, name, register, prefix=None, suffix=None, separator=None):
        if name.startswith("_"):
            raise ValueError(f"Segment name is not allowed to start with underscore: {name}")
        self.name = name
        self.register = register
        self.entries = []
        self.register[name] = self
        if prefix is not None:
            self.prefix = prefix
        if suffix is not None:
            self.suffix = suffix
        if separator is not None:
            self.separator = separator

    def add(self, entry, to_beginning=False):
        if to_beginning:
            self.entries = [entry] + self.entries
        else:
            self.entries.append(entry)
        if isinstance(entry, Segment):
            if entry.name in self.register:
                if id(self.register[entry.name]) != id(entry):
                    raise Exception(f"Duplicate segment: {entry.name}")
            else:
                self.register[entry.name] = entry
        return self

    def add_resource(self, resource, to_beginning=False):
        import lqreports.resource as rs

        if isinstance(resource, str):
            resource = rs.FileResource(resource)
        return self.add(ResourceHtmlLink(resource), to_beginning=to_beginning)

    def render(self, render_context=None):
        txt = str(self.prefix)
        sep = ""
        for i, entry in enumerate(self.entries):
            txt += sep
            sep = self.separator
            if isinstance(entry, str):
                txt += entry
            elif isinstance(entry, Renderable):
                txt += entry.render(render_context)
            else:
                raise Exception(
                    f"Unsupported entry type in {self.name}: {type(entry)}, entry number {i+1}"
                )
        txt += self.suffix
        return txt


class ResourceHtmlLink(Renderable):
    def __init__(self, resource, kind=None):
        self.resource = resource
        self.kind = resource.extension if kind is None else kind

    def render(self, render_context):
        if self.kind == "css":
            link = self.resource.link(render_context.link_type)
            return f"""    <link href="{link}" rel="stylesheet">"""
        elif self.kind == "js":
            link = self.resource.link(render_context.link_type)
            return f"""    <script src="{link}"></script>"""
        else:
            raise Exception(f"Unsupported kind: {self.kind}")


class HtmlHeader(Segment):
    prefix = "  <head>\n"
    suffix = "\n  </head>"
    separator = "\n"

    def __init__(self, register):
        super().__init__("header", register)


class HtmlBody(Segment):
    prefix = "  <body>\n"
    suffix = "\n  </body>"
    separator = "\n"

    def __init__(self, register):
        super().__init__("body", register)


class Scripts(Segment):
    separator = "\n"

    def __init__(self, register):
        super().__init__("scripts", register)


class HtmlDocument(Segment):
    prefix = "<html>\n"
    suffix = "\n</html>"
    separator = "\n"

    def __init__(self, register, title="Document"):
        super().__init__("document", register)
        self.add(HtmlHeader(register))
        self.add(HtmlBody(register))
        self.register.body.add(Segment("content", register))
        self.register.body.add(Scripts(register))
        self.title = title
        self.register.header.add(f"<title>{title}</title>")


class VuetifyApp(Segment):
    prefix = """<div id="app">
    <v-app>
"""
    suffix = """
    </v-app>
  </div>
"""


class VuetifyPanel(Segment):
    def __init__(self, name, register, fluid=False):
        super().__init__(
            name=name,
            register=register,
            prefix=f"""<v-container {"fluid" if fluid else ""} v-if='visible_panel=="{name}"'>\n""",
            suffix="""</v-container>\n""",
        )

    def dataframe_view(
        self,
        name="dataframe",
        items_per_page=10,
        attr='class="elevation-1"',
        show_select=False,
        single_select=True,
        row_action_icon="mdi-eye",
    ):
        code = ""
        if show_select:
            code += f""" show-select single-select='{"true" if single_select else "false"}' """
            code += """ v-model='selected' """
#        template_code = (
#            """
#        <template v-slot:item.rowid="{ item }">
#            <v-btn v-if="is_admin()" @click="row_action(item.rowid)">
#                Edit
#            </v-btn>
#        </template>
        template_code = (
            """
        <template v-slot:item.hours="props">
            <v-edit-dialog
            :return-value.sync="props.item.hours"
            @save="save"
            @cancel="cancel"
            @open="open"
            @close="close"
            >
            {{format_hours(props.item.hours)}}
            <template v-slot:input>
                <v-text-field
                v-if="is_admin()"
                v-model="props.item.hours"
                label="Edit"
                single-line
                ></v-text-field>
                <v-btn v-if="!is_admin()" @click="show_panel('admin_panel')">Login</v-btn>
            </template>
            </v-edit-dialog>
        </template>
        """)
        self.add(
            f"""
        <v-card>
            <v-card-title>
            <v-text-field
                v-model="search"
                append-icon="mdi-magnify"
                label="Search"
                single-line
                hide-details
            ></v-text-field>
            </v-card-title>
            <v-data-table
                %s
                :headers="{name}_headers"
                :items="{name}_data"
                :items-per-page="{items_per_page}"
                {attr}
                :search="search"
            >
            {template_code}
            </v-data-table>
        </v-card>        
        """
            % code
        )

    def row_detail(self, title_index=1):
        import html

        # df = self.register.document.df
        labels = self.register.document.labels
        html = """
        <v-card>
          <v-card-title>{{selected_row[%d]}}</v-card-title>
          <v-card-text>
%s
          </v-card-text>
        </v-card>
        """ % (
            title_index,
            "\n".join(
                f"""
            <v-row>
              <v-col>{html.escape(label)}:</v-col>
              <v-col>%s</v-col>
            </v-row>
        """
                % ("{{selected_row.%s}}" % label)
                for i, label in enumerate(labels)
                if i > 0
            ),
        )
        self.add(html)
        return self

    def switch(self, model, label=None, value=None):
        if label is None:
            label = model
        if value is not None:
            self.register.vuetify_script.add_data(model, value)
        self.add(f"<v-switch v-model='{model}' label='{label}'></v-switch>")
        return self

    def checkbox(self, model, label=None, value=None):
        if label is None:
            label = model
        if value is not None:
            self.register.vuetify_script.add_data(model, value)
        self.add(f"<v-checkbox v-model='{model}' label='{label}'></v-checkbox>")
        return self

    def textfield(self, model, label=None, value=None, hint=None, attr=""):
        if label is None:
            label = model
        if value is not None:
            self.register.vuetify_script.add_data(model, value)
        if hint is not None:
            attr += f" hint='{hint}'"
        self.add(
            f"<v-text-field v-model='{model}' label='{label}' {attr}></v-text-field>"
        )
        return self

    def textfield(self, model, label=None, value=None, hint=None, attr=""):
        if label is None:
            label = model
        if value is not None:
            self.register.vuetify_script.add_data(model, value)
        if hint is not None:
            attr += f" hint='{hint}'"
        self.add(f"<v-textarea v-model='{model}' label='{label}' {attr}></v-textarea>")
        return self

    def figure(self, fig, extension="svg", max_width=800, max_height=600):
        assert extension in ("png", "svg", "pdf", "ps", "eps")
        output = BytesIO()
        fig.savefig(output, dpi=300, format=extension)
        url = dataurl(output.getvalue(), mimetype_from_extension(extension))
        html = f"""<v-img src="{url}" max-height="{max_height}" max-width="{max_width}"></v-img>"""
        self.add(html)
        return self

    def image(self, path, max_width=800, max_height=600):
        extension = path.split(".")[-1]
        assert extension in ("png", "svg", "jpg", "jpeg", "gif")
        data = open(path, "rb").read()
        url = dataurl(data, mimetype_from_extension(extension))
        html = f"""<v-img src="{url}" max-height="{max_height}" max-width="{max_width}"></v-img>"""
        self.add(html)
        return self

    def liquer_logo(self):
        path = str(resources_path() / "liquer.png")
        return self.image(path, max_width=500, max_height=707)

    def chart(self, model, value=None, attr=""):
        self.add(f"""<plotly-chart :chart="{model}" {attr}></plotly-chart>""")
        if value is not None:
            self.register.vuetify_script.add_data(model, value)
        return self

    def _item_attributes(self, arg):
        icon = arg.get("icon")
        click = arg.get("click")
        href = arg.get("href")
        to = arg.get("to")
        color = arg.get("color")
        style = arg.get("style")
        attr = arg.get("attr")
        panel = arg.get("panel")

        item_attributes = ""
        if click is not None:
            if panel is not None:
                raise Exception(
                    f"Using both click and panel at the same time is not supported."
                )
            item_attributes += f""" @click="{click}" """
        if href is not None:
            item_attributes += f""" href="{href}" """
        if to is not None:
            item_attributes += f""" to="{to}" """
        if color is not None:
            item_attributes += f""" color="{color}" """
        if style is not None:
            item_attributes += f""" style="{style}" """
        if attr is not None:
            item_attributes += f""" {attr} """
        if panel is not None:
            if "panels" not in self.register:
                raise Exception(f"Panels not available, use .with_panels() method.")
            if panel not in self.register:
                raise Exception(f"Panel {panel} not available, use .panel() method.")
            item_attributes += f""" @click="show_panel('{panel}')" """

        return item_attributes

    def button(
        self,
        title,
        icon=None,
        click=None,
        href=None,
        to=None,
        color=None,
        style=None,
        attr=None,
        panel=None,
    ):
        item_attributes = self._item_attributes(
            dict(
                icon=icon,
                click=click,
                href=href,
                to=to,
                color=color,
                style=style,
                attr=attr,
                panel=panel,
            )
        )

        icon_code = "" if icon is None else f"<v-icon>{icon}</v-icon>"
        if title is None:
            title = ""
        text = f"""
        <v-btn {item_attributes} {"" if icon is None else "icon"}>{icon_code}{title}</v-btn>
        """
        self.add(text)
        return self


class VuetifyComponent(Segment):
    def __init__(self, name, register):
        super().__init__(
            name,
            register,
            prefix="""Vue.component("%s", {\n""" % name,
            suffix="""\n});\n""",
        )
        self.component_name = name
        r = self.register
        self.add("  data: function() {\n")
        self.add("    return {\n")
        self.data_segment = Segment(f"{name}__data", r, separator=",\n") 
        self.add(self.data_segment)
        self.add("\n    };\n},\n")
        self.add("  template: '")
        self.template_segment = Segment(f"{name}__template", r)
        self.add(self.template_segment)
        self.add("'\n")

    def add_data(self, name, value=None, raw=False):
        import json

        data_segment = self.data_segment
        if raw:
            data_segment.add(f"        {name}: {value}")
        else:
            if value is None:
                data_segment.add(f"        {name}: null")
            elif isinstance(value, str):
                data_segment.add(f"        {name}: {repr(value)}")
            elif (
                isinstance(value, dict)
                or value in (True, False)
                or isinstance(value, list)
            ):
                data_segment.add(f"        {name}: {json.dumps(value)}")
            else:
                data_segment.add(f"        {name}: {value}")
        return self

    def add_template(self, text):
        self.template_segment.add(text.replace("\n", "\\n"))
        return self


class VuetifyScript(Segment):
    def __init__(self, register):
        super().__init__("vuetify_script", register)
        r = self.register
        self.add("    <script>\n")
        self.add(Segment("before_init_vue", r))
        self.add(Segment("init_vue", r))
        self.add(Segment("vue_components", r))
        self.add(
            """
    new Vue({
      el: '#app',
      vuetify: new Vuetify({
        icons: {
            iconfont: 'mdi', // 'mdi' || 'mdiSvg' || 'md' || 'fa' || 'fa4' || 'faSvg'
        },
      }),
      data: {
"""
        )
        vue_data = Segment("vue_data", r, separator=",\n")
        self.add(vue_data)
        self.add(
            """
      },
      methods: {
"""
        )
        self.add(Segment("vue_methods", r, separator=",\n"))
        self.add(
            """
      },
      computed: {
"""
        )
        self.add(Segment("vue_computed", r, separator=",\n"))
        self.add(
            """
      },
      created: function() {
"""
        )
        self.add(Segment("vue_created", r))
        self.add(
            """
      },
      watch: {
"""
        )
        self.add(Segment("vue_watch", r, separator=",\n"))
        self.add(
            """
      }
"""
        )

        self.add(Segment("vue_other", r))
        self.add(
            """
    });
"""
        )
        self.add(Segment("init_vue_after", r))
        self.add("    </script>\n")

    def add_data(self, name, value=None, raw=False):
        import json

        if raw:
            self.register.vue_data.add(f"        {name}: {value}")
        else:
            if value is None:
                self.register.vue_data.add(f"        {name}: null")
            elif isinstance(value, str):
                self.register.vue_data.add(f"        {name}: {repr(value)}")
            elif (
                isinstance(value, dict)
                or value in (True, False)
                or isinstance(value, list)
            ):
                self.register.vue_data.add(f"        {name}: {json.dumps(value)}")
            else:
                self.register.vue_data.add(f"        {name}: {value}")
        return self

    def add_method(self, name, function):
        self.register.vue_methods.add(f"        {name}: {function}")
        return self

    def add_computed(self, name, get_code, set_code=None):
        if set_code is None:
            code = "function(){" + get_code + "}"
        else:
            get_code_function = "function(){" + get_code + "}"
            set_code_function = "function(value){" + set_code + "}"
            code = (
                "{\n        get:"
                + get_code_function
                + ",\n        set:"
                + set_code_function
                + "}"
            )
        self.register.vue_computed.add(f"        {name}: {code}")
        return self

    def add_watch(self, name, function):
        self.register.vue_watch.add(f"        {name}: {function}")
        return self

    def add_created(self, code):
        self.register.vue_created.add(code)
        return self

    def component(self, name):
        c = VuetifyComponent(name, self.register)
        self.register.vue_components.add(c, self.register)
        return c


class VuetifyDocument(HtmlDocument):
    def __init__(self, register, title="Document"):
        super().__init__(register, title=title)
        self.register.header.add_resource("materialdesignicons")
        self.register.header.add_resource("vuetify_css")
        self.register.content.add(VuetifyApp("app", register))
        self.register.app.add(
            Segment("v_main", register, prefix="<v-main>\n", suffix="</v-main>\n")
        )
        self.register.scripts.add_resource("vue")
        self.register.scripts.add_resource("vue_resource")
        self.register.scripts.add_resource("vuetify")
        self.register.scripts.add(VuetifyScript(register))


class VuetifyDashboard(VuetifyDocument):
    def __init__(self, register, title="Document"):
        super().__init__(register, title=title)

    def with_navigation_drawer(self):
        r = self.register
        r.vuetify_script.add_data("app_drawer", False)
        r.app.add(
            Segment(
                "navigation_drawer",
                r,
                prefix="""
        <v-navigation-drawer v-model="app_drawer" app >
          <v-list>
""",
                suffix="""        </v-list>\n          </v-navigation-drawer>\n""",
            )
        )
        return self

    def with_panels(self):
        r = self.register
        r.app.add(Segment("panels", r))
        r.vuetify_script.add_data("visible_panel", "home_panel")
        r.vuetify_script.add_method(
            "show_panel",
            """
        function(panel){
            console.log("Show",panel);
            this.visible_panel=panel;
            this.app_drawer=false;
            this.store();
            this.dataframe_json="";
            this.names_json="";
        }"""
        )
        self.panel("home_panel")
        return self

    def panel(self, name, fluid=False):
        r = self.register
        panel = VuetifyPanel(name, r, fluid=fluid)
        r.v_main.add(panel)
        return panel

    def add_drawer_item_raw(self, entry):
        if "navigation_drawer" not in self.register:
            self.with_navigation_drawer()
        self.register.navigation_drawer.add(entry)

    def _item_attributes(self, arg):
        icon = arg.get("icon")
        click = arg.get("click")
        href = arg.get("href")
        to = arg.get("to")
        color = arg.get("color")
        style = arg.get("style")
        attr = arg.get("attr")
        panel = arg.get("panel")

        item_attributes = ""
        if click is not None:
            if panel is not None:
                raise Exception(
                    f"Using both click and panel at the same time is not supported."
                )
            item_attributes += f""" @click="{click}" """
        if href is not None:
            item_attributes += f""" href="{href}" """
        if to is not None:
            item_attributes += f""" to="{to}" """
        if color is not None:
            item_attributes += f""" color="{color}" """
        if style is not None:
            item_attributes += f""" style="{style}" """
        if attr is not None:
            item_attributes += f""" {attr} """
        if panel is not None:
            if "panels" not in self.register:
                raise Exception(f"Panels not available, use .with_panels() method.")
            if panel not in self.register:
                raise Exception(f"Panel {panel} not available, use .panel() method.")
            item_attributes += f""" @click="show_panel('{panel}')" """

        return item_attributes

    def drawer_item(
        self,
        title,
        icon=None,
        click=None,
        href=None,
        to=None,
        color=None,
        style=None,
        attr=None,
        panel=None,
    ):
        if "navigation_drawer" not in self.register:
            self.with_navigation_drawer()
        item_attributes = self._item_attributes(
            dict(
                icon=icon,
                click=click,
                href=href,
                to=to,
                color=color,
                style=style,
                attr=attr,
                panel=panel,
            )
        )

        icon_code = (
            ""
            if icon is None
            else f"<v-list-item-icon><v-icon>{icon}</v-icon></v-list-item-icon>"
        )
        text = f"""
        <v-list-item {item_attributes}>
            {icon_code}
            <v-list-item-title>{title}</v-list-item-title>
        </v-list-item>
        """
        self.register.navigation_drawer.add(text)
        return self

    def with_app_bar(self, title=None, color=None, attr=None, style=None):
        title = self.title if title is None else title
        attributes = self._item_attributes(
            dict(
                color=color,
                style=style,
                attr=attr,
            )
        )
        r = self.register
        admintime="{{remaining_admintime()}}"
        r.app.add(
            Segment(
                "app_bar",
                r,
                prefix=f"""
        <v-app-bar app :color="is_admin()?'red':'primary'">
            <v-app-bar-nav-icon @click="app_drawer = !app_drawer"></v-app-bar-nav-icon>
            <v-toolbar-title>{title} &nbsp;</v-toolbar-title>
            <v-btn v-if="is_admin()" @click="logout()">Logout</v-btn>
""",
                suffix=f"</v-app-bar>\n",
            )
        )
        return self

    def add_bar_button(
        self,
        title,
        icon=None,
        click=None,
        href=None,
        to=None,
        color=None,
        style=None,
        attr=None,
        panel=None,
    ):
        if "app_bar" not in self.register:
            self.with_app_bar()
        item_attributes = self._item_attributes(
            dict(
                icon=icon,
                click=click,
                href=href,
                to=to,
                color=color,
                style=style,
                attr=attr,
                panel=panel,
            )
        )

        icon_code = "" if icon is None else f"<v-icon>{icon}</v-icon>"
        if title is None:
            title = ""
        text = f"""
        <v-btn {item_attributes} {"" if icon is None else "icon"}>{icon_code}{title}</v-btn>
        """
        self.register.app_bar.add(text)
        return self

    def add_bar_menu(self, title, menu):
        if "app_bar" not in self.register:
            self.with_app_bar()
        self.register.app_bar.add(
            """
        <v-menu offset-y>
            <template v-slot:activator="{ on }">
                <v-btn text v-on="on">%s</v-btn>
            </template>
            <v-list>\n"""
            % title
        )
        for menu_item in menu:
            title = menu_item.get("title")
            icon = menu_item.get("icon")
            item_attributes = self._item_attributes(menu_item)

            icon_code = "" if icon is None else f"<v-icon>{icon}</v-icon>"
            if title is None:
                title = ""
            text = f"""
                <v-list-item {item_attributes}>
                    <v-list-item-title>{title}</v-list-item-title>
                </v-list-item>\n"""
            self.register.app_bar.add(text)
        self.register.app_bar.add(
            """   
            </v-list>
        </v-menu>\n"""
        )
        return self

    def add_bar_spacer(self):
        if "app_bar" not in self.register:
            self.with_app_bar()
        self.register.app_bar.add("<v-spacer></v-spacer>")
        return self

    def with_plotly(self):
        r = self.register
        r.scripts.add_resource("plotly")
        r.init_vue.add(
            """
Vue.component("plotly-chart", {
  props: ["chart"],
  template: '<div :ref="chart.uuid"></div>',
  mounted() {
    Plotly.plot(this.$refs[this.chart.uuid], this.chart.traces, this.chart.layout);
  },
  watch: {
    chart: {
      handler: function() {
        Plotly.react(
          this.$refs[this.chart.uuid],
          this.chart.traces,
          this.chart.layout,
          this.chart.config
        );
      },
      deep: true
    }
  }
});        
        """
        )
        return self

    def with_dataframe(
        self, df, name="dataframe", labels=None, with_rowid=True, rowid_column="rowid"
    ):
        if labels is None:
            labels = list(df.columns)
        if with_rowid:
            assert rowid_column not in df.columns
            columns = [rowid_column] + [c for c in df.columns]
            df = df.copy()
            df[rowid_column] = np.arange(len(df))
            df = df[columns]
            labels = [rowid_column] + labels
        self.df = df
        self.labels = labels
        r = self.register
        script = r.vuetify_script
        script.add_data(name, df.to_json(orient="table"), raw=True)
        script.add_data("search", "")
        script.add_data("selected", [])
        script.add_data(f"{name}_data", [])
        script.add_created(f"this.{name}_data=this.{name}.data;\n")
        script.add_data(
            f"{name}_headers",
            [
                dict(text=label, value=label, sortable=True)
                for i, label in enumerate(labels)
            ],
        )
        return self

    def with_row_action(self, code):
        r = self.register
        script = r.vuetify_script
        script.add_method("row_action", "function(rowid){%s}" % code)
        return self

    def with_panel_row_action(self, panel_name):
        r = self.register
        script = r.vuetify_script
        script.add_data("selected_rowid")
        script.add_data("selected_row", [])
        return self.with_row_action(
            f"""
        this.selected_rowid=rowid;
        this.selected_row=this.dataframe.data[rowid];
        this.show_panel('{panel_name}');
        """
        )
