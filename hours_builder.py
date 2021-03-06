import sys
sys.path.append("..")

import matplotlib.pyplot as plt
from lqreports.segments import *
from pathlib import Path

def render(use_liquerstore, init_from_localstore, use_dataurl=False):
    r = Register()
    doc = (
        VuetifyDashboard(r, "Working Hours Registration")
        .with_navigation_drawer()
        .with_app_bar(color="primary")
        .with_panels()
    )
    r.header.add("""
  <!-- Responsive -->
  <meta charset="utf-8">
  <meta name="viewport"content="width=device-width, initial-scale=1">
  <meta http-equiv="X-UA-Compatible" content="ie=edge">
    
  <!-- Meta Tags requred for Progressive Web App -->
  <meta name="apple-mobile-web-app-status-bar" content="#aa7700">
  <meta name="theme-color" content="black">
  
  <!-- Manifest File link -->
  <link rel="manifest" href="manifest.json">    
    """)
    r.before_init_vue.add("""
    window.addEventListener('load', function(){registerSW();});
  
    async function registerSW() {
      if ('serviceWorker' in navigator) {
        try {
          await navigator.serviceWorker.register('serviceworker.js');
        }
        catch (e) {
          console.log('Service worker registration failed');
        }
      }
    }
    """)
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
            Working {{format_hours_min(last_hours(username))}}.
          </v-col>
      </v-row>

      <v-row>
      </v-row>

    """)
    doc.panel("overview_panel").add("""
      <h1>Overview</h1>
      <v-row>
          <v-col>
            <v-data-table
                
                :headers="overview_headers"
                :items="overview_all"
                :items-per-page="10"
                class="elevation-1"
                :search="search"
            >
            </v-data-table>
          </v-col>
      </v-row>
    """)
    doc.panel("admin_panel").add("""
    <v-row v-if="!is_admin()">
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
    <v-row v-if="!is_admin()">
      <v-col>
        <v-btn @click="login()">Login</v-btn>
      </v-col>
    </v-row>
    <v-row v-if="is_admin()">
      <v-col><v-btn @click="show_panel('names_edit_panel')">Edit names</v-btn></v-col>
    </v-row>
    <v-row v-if="is_admin()">
      <v-col><v-btn @click="erase()">Erase all data</v-btn></v-col>
      <v-col><v-checkbox v-model="confirm_erase" label="Confirm"></v-checkbox></v-col>
    </v-row>
    <v-row v-if="is_admin()">
      <v-col><v-btn @click="show_panel('raw_panel')">Edit raw data</v-btn></v-col>
    </v-row>
    """)
    doc.panel("names_edit_panel").add("""
    <v-row v-if="!is_admin()"><v-col>%s</v-col></v-row>
    <v-row v-if="is_admin()">
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
    doc.panel("raw_panel").add("""<h1>Raw data</h1>
    <v-card v-if="is_admin()">
    <v-row v-if="json_error.length"><v-col>
    <v-chip>{{json_error}}</v-chip>
    </v-col></v-row>
    <v-row><v-col>
    <v-btn @click="get_json()">get</v-btn>
    <v-btn @click="set_json()">set</v-btn>
    </v-col>
    </v-row>
    
    <v-row><v-col>
    <v-textarea solo v-model="names_json"></v-textarea>
    </v-col></v-row>
    <v-row><v-col>
    <v-textarea solo v-model="dataframe_json"></v-textarea>
    </v-col></v-row>
    </v-card>
    """)


    r.vuetify_script.add_method("login", """
    function(){
        this.confirm_erase=false;
        console.log("Login");
        if (this.adminpass=="raneejar1234"){
            this.admintime=Date.now();
            console.log("Login successful, is_admin:",this.is_admin());
        }
        else{
            this.admintime=0;
            console.log("Login failed, is_admin:",this.is_admin());
        }
        this.adminpass="";
    }
    """)
    r.vuetify_script.add_method("logout", """
    function(){
        console.log("Logout");
        this.admintime=0;
        this.adminpass="";
        this.show_panel("home_panel");
    }
    """)

    doc.drawer_item("Home", icon="mdi-home", panel="home_panel")
    doc.drawer_item("Overview", icon="mdi-table", panel="overview_panel")
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

    r.vuetify_script.add_method("overview", """
    function (name){
        if (name==null){
            name=this.username;
        }
        var data = this.dataframe.data.filter(function(x){
            return (x.name==name); 
        });
        const to_key = function(x){
            var month = ""+x.month;
            if (month.length==1){
                month="0"+month;
            }
            return x.year+"_"+month;
        };
        var keys=data.map(to_key);
        var ukeys = keys.filter(function(value,index,self){return self.indexOf(value)===index;});
        ukeys.sort();
        ukeys = ukeys.slice(Math.max(ukeys.length - 3, 0));
        var hours = {};
        var year = {};
        var month = {};
        for (var i=0; i<data.length; i++){
            var x = data[i];
            var h = parseFloat(x.hours);
            if (!isFinite(h)){
                h=0;
            }
            var key = to_key(x);
            year[key]=x.year;
            month[key]=x.month;
            if (key in hours){
                hours[key]+=h;
            }
            else{
                hours[key]=h;
            }
        }
        var summary=ukeys.map(function(key){
            return {name:name, year:year[key], month:month[key], hours:hours[key]};
        });
        return summary;
    }
    """)
    r.vuetify_script.add_computed("overview_all", """
        var all=[];
        for (var i=0; i<this.names.length; i++){
            var o = this.overview(this.names[i]);
            Array.prototype.push.apply(all,o);
        }
        return all;
    """)

    r.vuetify_script.add_method("start_working", """
    function (name){
        if (name==null){
            name=this.username;
        }
        console.log("Start",name);
        var d = new Date();
        this.dataframe.data.push({
            index:this.dataframe.data.length,
            rowid:this.dataframe.data.length,
            name:name,
            year:d.getFullYear(),
            month:d.getMonth()+1,
            start:d.toISOString(),
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
        this.dataframe.data[index].end = d.toISOString();
        //this.dataframe.data[index].hours = Math.trunc(this.last_hours(name)*2)/2;
        this.dataframe.data[index].hours = this.last_hours(name).toString();
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

    r.vuetify_script.add_method("format_hours", """
    function (hours){
        console.log("format_hours",hours);
        if (hours==null || hours==undefined || hours==NaN){
            return "";
        }
        var h = Math.trunc(hours);
        if (isNaN(h)){
            return "";
        }
        var m = Math.trunc(hours*60)-h*60;
        if (m==0){
            m= "00";
        }
        else{
          if (m<10){
              m = "0"+m;
          }
        }
        console.log("formated",hours,h,m);
        var hh= ""+h+":"+m;
        return hh;
    }
    """)
    r.vuetify_script.add_method("format_hours_min", """
    function (hours){
        console.log("format_hours_min",hours);
        if (hours==null || hours==undefined || hours==NaN){
            return "";
        }
        var h = Math.trunc(hours);
        if (isNaN(h)){
            return "";
        }
        var m = Math.trunc(hours*60)-h*60;
        if (h==0){
            h="";
        }
        else if (h==1){
            h=""+h+" hour,";
        }
        else{
            h=""+h+" hours,";
        }
        console.log("formated",hours,h,m);
        var hh= ""+h+" "+m+" minutes";
        return hh;
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

    r.vuetify_script.add_method("error", """
    function(message){
        console.log("ERROR",message);
        this.json_error=message;
    }
    """)

    if use_liquerstore:
        r.vuetify_script.add_method("store", """
        function(){
            this.store_liquerstore();
        }
        """)
        r.vuetify_script.add_method("restore", """
        function(){
            this.restore_liquerstore();
        }
        """)
    else:
        r.vuetify_script.add_method("store", """
        function(){
            this.store_localstore();
        }
        """)
        r.vuetify_script.add_method("restore", """
        function(){
            this.restore_localstore();
        }
        """)

    r.vuetify_script.add_method("store_localstore", """
    function(){
        localStorage.setItem("hours_dataframe",JSON.stringify(this.dataframe));
        localStorage.setItem("hours_names",JSON.stringify(this.names));       
    }
    """)
    r.vuetify_script.add_method("restore_localstore", """
    function(){
        try{
            this.json_error="OK";
            var dataframe = JSON.parse(localStorage.getItem("hours_dataframe"));
            if (dataframe!=null){
                this.dataframe=dataframe;                
            }
            else{
                this.json_error="Restore failed: null dataframe";      
            }
            var names = JSON.parse(localStorage.getItem("hours_names"));
            if (names!=null){
                this.names=names;                
            }
            else{
                this.json_error="Restore failed: null names";      
            }
        }
        catch(e){
            this.json_error="Restore failed:"+e;
        }
    }
    """)

    r.vuetify_script.add_method("store_liquerstore", """
    function(){
      this.$http.post("/liquer/api/store/data/data/hours_dataframe.json", JSON.stringify(this.dataframe)).then(
        function (response) {
            console.log("posted hours dataframe",response);
        }.bind(this),
        function (reason) {
          this.error("Failed post data", reason);
        }.bind(this)
      )
      this.$http.post("/liquer/api/store/data/data/hours_names.json", JSON.stringify(this.names)).then(
        function (response) {
            console.log("posted names",response);
        }.bind(this),
        function (reason) {
          this.error("Failed post data", reason);
        }.bind(this)
      )
    }
    """)
    r.vuetify_script.add_method("restore_liquerstore", """
    function(){
        this.$http.get("/liquer/api/store/data/data/hours_dataframe.json").then(function (response) {
            response.json().then(function (data) {
                if (data.status!=undefined){
                    console.log("Error reading dataframe",data.message);
                    console.log("Data:",data);
                    this.dataframe={};
                }
                else{
                    this.dataframe = data;
                    console.log("Dataframe reading OK",data);
                }
            }.bind(this), function (reason) { this.error("Json error (reading dataframe)", reason); }.bind(this));
        }.bind(this), function (reason) { this.error("Error reading dataframe", reason); }.bind(this));
        this.$http.get("/liquer/api/store/data/data/hours_names.json").then(function (response) {
            response.json().then(function (data) {
                if (data.status!=undefined){
                    console.log("Error reading names",data.message);
                    console.log("Data:",data);
                    this.names=[];
                }
                else{
                    this.names = data;
                    console.log("Names reading OK",data);
                }
            }.bind(this), function (reason) { this.error("Json error (reading names)", reason); }.bind(this));
        }.bind(this), function (reason) { this.error("Error reading names", reason); }.bind(this));
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

    r.vuetify_script.add_method("get_json", """
    function(){
        this.dataframe_json=JSON.stringify(this.dataframe);
        this.names_json = JSON.stringify(this.names);
    }
    """)
    r.vuetify_script.add_method("set_json", """
    function(){
        try{
            this.json_error="";
            var dataframe = JSON.parse(this.dataframe_json);
            if (dataframe!=null){
                this.dataframe=dataframe;
            }
            else{
                this.json_error="Set JSON failed: dataframe is null";
            }
            var names = JSON.parse(this.names_json);
            if (names!=null){
                this.names=names;                
            }
            else{
                this.json_error="Set JSON failed: names is null";
            }
        }
        catch(e){
            this.json_error="Set JSON failed:"+e;
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
    r.vuetify_script.add_data("overview_headers", 
        [
            {"text": "Name", "value": "name", "sortable": True},
            {"text": "Year", "value": "year", "sortable": True},
            {"text": "Month", "value": "month", "sortable": True},
            {"text": "Hours", "value": "hours", "sortable": True}
        ]
    )
    r.vuetify_script.add_data("dataframe_json", "")
    r.vuetify_script.add_data("names_json", "")
    r.vuetify_script.add_data("json_error", "")

    # r.vuetify_script.add_method("test_store", """
    # function(){
    #   console.log('test_store');
    #   this.$http.get("/liquer/api/store/data/data/readme.txt").then(
    #     function (response) {
    #         console.log("response:",response.body);
    #     }.bind(this),
    #     function (reason) {
    #       this.error("Failed loading data", reason, query);
    #     }.bind(this)
    #   );
    #   this.$http.post("/liquer/api/store/data/data/test.txt", "Hello").then(
    #     function (response) {
    #         console.log("posted",response);
    #     }.bind(this),
    #     function (reason) {
    #       this.error("Failed post data", reason);
    #     }.bind(this)
    #   )
    # }
    # """)

    r.vuetify_script.add_method("is_admin", """
    function(){
       return this.remaining_admintime()>0;
    }
    """)

    r.vuetify_script.add_method("remaining_admintime", """
    function(){
       return (15-(Date.now()-this.admintime)/(60*1000));
    }
    """)

    if init_from_localstore:
        r.vuetify_script.add_created("""
        console.log('Start Hours');
        this.restore_localstore();
        """)
    else:
        r.vuetify_script.add_created("""
        console.log('Start Hours');
        this.restore();
        """)


    r.vuetify_script.add_method("save", """
    function(){
        this.snack = true
        this.snackColor = 'success'
        this.snackText = 'Data saved'
    }
    """)
    r.vuetify_script.add_method("cancel", """
    function(){
        this.snack = true
        this.snackColor = 'error'
        this.snackText = 'Canceled'
    }
    """)
    r.vuetify_script.add_method("open", """
    function(){
        this.snack = true
        this.snackColor = 'info'
        this.snackText = 'Dialog opened'
    }
    """)
    r.vuetify_script.add_method("close", """
    function(){
        console.log('Dialog closed')
    }
    """)

    if use_dataurl:
        return (doc.render(RenderContext(link_type=LinkType.DATAURL)))
    else:
        return (doc.render(RenderContext()))

if __name__ == '__main__':
    for use_liquerstore, init_from_localstore, path in [
        (False, False,"index.html"),
        (True, False,"app/dist/data/index.html"),
        (True, True, "app/dist/data/init.html"),
        (False, False, "app/dist/data/localstore.html"),
        (True, False,"app/data/index.html"),
        (True, True, "app/data/init.html"),]:
        (False, False, "app/data/localstore.html"),
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(path,"w") as f:
            f.write(render(use_liquerstore, init_from_localstore))
