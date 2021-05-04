import sys
sys.path.append("..")

import matplotlib.pyplot as plt
from lqreports.segments import *

if __name__ == '__main__':
    r = Register()
    doc = (
        VuetifyDashboard(r, "Working Hours Registration")
        .with_navigation_drawer()
        .with_app_bar(color="primary")
        .with_panels()
    )
    login_button="""<v-btn @click="show_panel('admin_panel')">Login</v-btn>"""
    doc.panel("home_panel", fluid=True).add("""
      <v-row v-for="n in names">
          <v-col>
            <v-btn @click="set_user(n)">{{n}}</v-btn>
          </v-col>
      </v-row>
      """
    )
    doc.panel("user_panel").add("<h1>{{username}}</h1>")
    doc.panel("user_panel").add("""
      <v-row>
          <v-col>
            <v-btn color="blue" large @click="show_panel('home_panel')">Home</v-btn>
          </v-col>
          <v-col v-if="!is_started(username)">
            <v-btn color="green" large @click="start_working(username)">Start</v-btn>
          </v-col>
          <v-col v-if="is_started(username)">
            <v-btn color="red" large @click="stop_working(username)">Stop</v-btn>
            Working {{last_hours(username)}} hours.
          </v-col>
      </v-row>

      <v-row>
      </v-row>

    """)
    doc.panel("admin_panel").add("""
    <v-row v-if="!is_admin">
      <v-col>
        <v-text-field
            v-model="adminpass"
            :append-icon="show1 ? 'mdi-eye' : 'mdi-eye-off'"
            :type="show1 ? 'text' : 'password'"
            name="input-pass"
            label="Password"
            hint="Enter the admin password"
            @click:append="show1 = !show1"
            @input = "login()"
          ></v-text-field>
      </v-col>
    </v-row>
    <v-row v-if="!is_admin">
      <v-col>
        <v-btn @click="login()">Login</v-btn>
      </v-col>
    </v-row>
    <v-row v-if="is_admin">
      <v-col><v-btn @click="show_panel('names_edit_panel')">Edit names</v-btn></v-col>
    </v-row>
    <v-row v-if="is_admin">
      <v-col><v-btn @click="erase()">Erase all data</v-btn></v-col>
      <v-col><v-checkbox v-model="confirm_erase" label="Confirm"></v-checkbox></v-col>
    </v-row>
    """)
    doc.panel("names_edit_panel").add("""
    <v-row v-if="!is_admin"><v-col>%s</v-col></v-row>
    <v-row v-if="is_admin">
    <v-col>
      <v-row v-for="(n, index) in names" :key="index">
          <v-col>
            <v-btn fab @click='up(n)'><v-icon>mdi-chevron-up</v-icon></v-btn>
            <v-btn fab @click='down(n)'><v-icon>mdi-chevron-down</v-icon></v-btn>
            <v-btn fab @click='remove(n)'><v-icon>mdi-close</v-icon></v-btn>
          </v-col>
          <v-col>
            <v-btn @click="set_user(n)">{{n}}</v-btn>
          </v-col>
      </v-row>
      <v-row>
          <v-col>
            <v-btn fab @click='new_user()'><v-icon>mdi-plus</v-icon></v-btn>
          </v-col>
          <v-col>
            <v-text-field outline v-model="new_username"></v-text-field>
          </v-col>
      </v-row>

    </v-col>
    </v-row>
    """%login_button)
    doc.panel("detail_panel").add("<h1>Edit hours - {{username}}</h1>")
#    doc.panel("edit_panel").add("""<h1>Edit hours - {{username}}</h1>""")
    doc.panel("login_panel").add("""
    <v-row>
      <v-col>
        <v-text-field
            v-model="adminpass"
            :append-icon="show1 ? 'mdi-eye' : 'mdi-eye-off'"
            :type="show1 ? 'text' : 'password'"
            name="input-pass"
            label="Password"
            hint="Enter the admin password"
            @click:append="show1 = !show1"
          ></v-text-field>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-btn @click="login()">Login</v-btn>
      </v-col>
    </v-row>
    """)

    r.vuetify_script.add_method("login", """
    function(){
        this.confirm_erase=false;
        console.log("Login");
        if (this.adminpass=="raneejar1234"){
            this.admintime=Date.now();
            console.log("Login successful, is_admin:",this.is_admin);
        }
        else{
            this.admintime=0;
            console.log("Login failed, is_admin:",this.is_admin);
        }
        this.adminpass="";
    }
    """)

    doc.drawer_item("Home", icon="mdi-home", panel="home_panel")
    doc.drawer_item("Admin", icon="mdi-account", panel="admin_panel")
    #doc.drawer_item("Ranees", href="http://www.ranees.dk")
 
    df=pd.DataFrame(dict(
        name=["test"],
        year=[2021],
        month=[4],
        start=[""],
        end=[""],
        hours=[""]))
 
    doc.with_dataframe(df).with_panel_row_action("detail_panel")
    #r.vuetify_script.add_data("myfilter",False)
    r.vuetify_script.add_method("update_user_filter", """
    function(){
        console.log("Update user filter",this.username);
        var u = this.username;
        if (this.username){
            this.dataframe_data = this.dataframe.data.filter(function(x){
                return (x.name==u); 
            });
        }
        else{
            this.dataframe_data = [];
        }
    }
    """)
    r.vuetify_script.add_method("up", """
    function(n){
        console.log("Up",n);
        for (var i=1; i<this.names.length; i++){
            if (this.names[i]==n){
                this.names[i]=this.names[i-1];
                this.names[i-1]=n;
                this.$forceUpdate();
                return;
            }
        }
    }
    """)
    r.vuetify_script.add_method("down", """
    function(n){
        for (var i=0; i<this.names.length-1; i++){
            if (this.names[i]==n){
                this.names[i]=this.names[i+1];
                this.names[i+1]=n;
                this.$forceUpdate();
                return;
            }
        }
    }
    """)
    r.vuetify_script.add_method("remove", """
    function(n){
        console.log("Remove",n);
        this.names = this.names.filter(function(x){
            return (x!=n); 
        });
        this.store();
    }
    """)
    r.vuetify_script.add_method("new_user", """
    function(){
        console.log("New user",this.new_username);
        this.names.push(this.new_username);
        this.new_username="";
        this.store();
    }
    """)
    r.vuetify_script.add_method("set_user", """
    function(username){
        console.log("Set user",username);
        this.username = username;
        this.show_panel("user_panel");
    }
    """)

    # r.vuetify_script.add_method("format_time", """
    # function(datems){
    #     var d = new Date(datems);
    #     var m=d.getMinutes();
    #     if (m==0){
    #         m="00";
    #     }
    #     else if (m<10){
    #         m="0"+m;
    #     }
    #     else{
    #         m=""+m;
    #     }
    #     return d.getHours()+":"+m;
    # }
    # """)

    # r.vuetify_script.add_method("format_hours", """
    # function(t){
    #     var h=Math.floor(t);
    #     var m=Math.floor(Math.floor((t-h)*60));
    #     if (m<10){m="0"+m;}
    #     return h+":"+m;
    # }
    # """)

    r.vuetify_script.add_method("start_working", """
    function (name){
        if (name==null){
            name=this.username;
        }
        console.log("Start",name);
        var d = new Date();
        this.dataframe.data.push({
            rowid:this.dataframe.data.length,
            name:name,
            year:d.getFullYear(),
            month:d.getMonth()+1,
            start:d.toString(),
            end:"",
            hours:"???",
        });
        this.store();
        this.update_user_filter();
    }
    """)

    r.vuetify_script.add_method("stop_working", """
    function (name){
        if (name==null){
            name=this.username;
        }
        console.log("Stop",name);
        if (!this.is_started(name)){
            console.log("Stop ignored since not started",name);
            return;
        }
        var d = new Date();
        var index = this.last_index(name);
        if (index==null){
            console.log("Stop ignored - no last",name);
            return;
        }
        this.dataframe.data[index].end = d.toString();
        this.dataframe.data[index].hours = Math.trunc(this.last_hours(name)*2)/2;
        this.store();
        this.update_user_filter();
    }
    """)

    r.vuetify_script.add_method("last_index", """
    function (name){
        if (name==null){
            name=this.username;
        }
        var index=null;
        for(var i=0;i<this.dataframe.data.length;i++){
            if (this.dataframe.data[i].name==name){
                index=i;
            }
        }
        return index;
    }
    """)

    r.vuetify_script.add_method("last_hours", """
    function (name){
        var index=this.last_index(name);
        if (index!=null){
            var r = this.dataframe.data[index];
            var start = r.start;
            return ((Date.now()-Date.parse(start))/1000/60/60);
        }
        return null;
    }
    """)

    r.vuetify_script.add_method("is_started", """
    function (name){
        console.log("Is started",name);
        var index=this.last_index(name);
        console.log(" - index",index);
        if (index!=null){
            var r = this.dataframe.data[index];
            if (r.end == ""){
                var start = r.start;
                var hours = this.last_hours(name);
                console.log(" - hours",hours);
                return (hours < 20);
            }
        }
        return false;
    }
    """)

    r.vuetify_script.add_method("store", """
    function(){
        localStorage.setItem("hours_dataframe",JSON.stringify(this.dataframe));
        localStorage.setItem("hours_names",JSON.stringify(this.names));
    }
    """)
    r.vuetify_script.add_method("restore", """
    function(){
        var dataframe = JSON.parse(localStorage.getItem("hours_dataframe"));
        if (dataframe!=null){
            this.dataframe=dataframe;                
        }
        var names = JSON.parse(localStorage.getItem("hours_names"));
        if (names!=null){
            this.names=names;                
        }
    }
    """)

    r.vuetify_script.add_method("erase", """
    function(){
        if (this.confirm_erase){
            this.dataframe={data:[]};
            this.names=[];
            this.confirm_erase=false;
            this.store();
        }
    }
    """)

    r.vuetify_script.add_watch("username", "function(new_value,old_value){console.log('watch',new_value,old_value);this.update_user_filter();}")

    r.user_panel.dataframe_view()
    r.detail_panel.add("""{{selected_row}}""")
    r.detail_panel.add("""<h2>Selected</h2>{{selected_row}}""")
    r.detail_panel.row_detail()

    r.vuetify_script.add_data("username", None)
    r.vuetify_script.add_data("new_username", "")
    r.vuetify_script.add_data("show1", False)
    r.vuetify_script.add_data("adminpass", "")
    r.vuetify_script.add_data("admintime", 0)
    r.vuetify_script.add_data("confirm_erase", False)
    r.vuetify_script.add_data("names", ["A","B"])

    r.vuetify_script.add_computed("is_admin", "return (Date.now()-this.admintime)<30*60*1000;")

    r.vuetify_script.add_created("""
      console.log('Start Hours');
      this.restore();
    """)

    print(doc.render(RenderContext(link_type=LinkType.LINK)))
