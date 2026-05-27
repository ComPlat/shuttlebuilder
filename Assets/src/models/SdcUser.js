import {SdcModel, SdcQuerySet} from 'sdc_client';

export default class SdcUser extends SdcModel {


  static fields = {
      "logentry_set": {
        "type": "ForeignKey",
        "required": false,
        "max_length": null,
        "is_relation": true,
        "many_to_many": false,
        "one_to_many": true,
        "many_to_one": false,
        "one_to_one": false,
        "related_model": "LogEntry",
        "remote_field": "user"
      },
      "elnuser": {
        "type": "OneToOneField",
        "required": false,
        "max_length": null,
        "is_relation": true,
        "many_to_many": false,
        "one_to_many": false,
        "many_to_one": false,
        "one_to_one": true,
        "related_model": "ElnUser",
        "remote_field": "user"
      },
      "shuttleinstance_set": {
        "type": "ForeignKey",
        "required": false,
        "max_length": null,
        "is_relation": true,
        "many_to_many": false,
        "one_to_many": true,
        "many_to_one": false,
        "one_to_one": false,
        "related_model": "ShuttleInstance",
        "remote_field": "owner"
      },
      "id": {
        "type": "BigAutoField",
        "required": false,
        "max_length": null,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "password": {
        "type": "CharField",
        "required": true,
        "max_length": 128,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "last_login": {
        "type": "DateTimeField",
        "required": false,
        "max_length": null,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "is_superuser": {
        "type": "BooleanField",
        "required": true,
        "max_length": null,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "username": {
        "type": "CharField",
        "required": true,
        "max_length": 150,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "first_name": {
        "type": "CharField",
        "required": false,
        "max_length": 150,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "last_name": {
        "type": "CharField",
        "required": false,
        "max_length": 150,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "email": {
        "type": "CharField",
        "required": false,
        "max_length": 254,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "is_staff": {
        "type": "BooleanField",
        "required": true,
        "max_length": null,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "is_active": {
        "type": "BooleanField",
        "required": true,
        "max_length": null,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "date_joined": {
        "type": "DateTimeField",
        "required": true,
        "max_length": null,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "email_confirmed": {
        "type": "BooleanField",
        "required": true,
        "max_length": null,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "groups": {
        "type": "ManyToManyField",
        "required": false,
        "max_length": null,
        "is_relation": true,
        "many_to_many": true,
        "one_to_many": false,
        "many_to_one": false,
        "one_to_one": false,
        "related_model": "Group",
        "remote_field": "user"
      },
      "user_permissions": {
        "type": "ManyToManyField",
        "required": false,
        "max_length": null,
        "is_relation": true,
        "many_to_many": true,
        "one_to_many": false,
        "many_to_one": false,
        "one_to_one": false,
        "related_model": "Permission",
        "remote_field": "user"
      }
    }

  constructor(data = {}) {
    super("SdcUser");
    this._toManyFields = [];
    this._logentry_set = new SdcQuerySet('LogEntry');
    this._toManyFields.push([this._logentry_set, 'user']);
    this._elnuser = new SdcQuerySet('ElnUser');
    this._shuttleinstance_set = new SdcQuerySet('ShuttleInstance');
    this._toManyFields.push([this._shuttleinstance_set, 'owner']);
    this._id = null;
    this._password = null;
    this._last_login = null;
    this._is_superuser = null;
    this._username = null;
    this._first_name = null;
    this._last_name = null;
    this._email = null;
    this._is_staff = null;
    this._is_active = null;
    this._date_joined = null;
    this._email_confirmed = null;
    this._groups = new SdcQuerySet('Group');
    this._toManyFields.push([this._groups, 'user']);
    this._user_permissions = new SdcQuerySet('Permission');
    this._toManyFields.push([this._user_permissions, 'user']);
    this.setValues(data);
  }

  setValues(data = {}) {
    data.id ??= data.pk ?? null;
    try {
    this.logentry_set.setFilter({ user:  data.id });
    this.logentry_set = data.logentry_set || [];
    } catch {} 
    try {
      if (data.elnuser) { this.elnuser = data.elnuser; }
    } catch {} 
    try {
    this.shuttleinstance_set.setFilter({ owner:  data.id });
    this.shuttleinstance_set = data.shuttleinstance_set || [];
    } catch {} 
    try {
      this.id = data.id ?? null;
    } catch {} 
    try {
      this.password = data.password ?? null;
    } catch {} 
    try {
      this.last_login = data.last_login ?? null;
    } catch {} 
    try {
      this.is_superuser = data.is_superuser ?? null;
    } catch {} 
    try {
      this.username = data.username ?? null;
    } catch {} 
    try {
      this.first_name = data.first_name ?? null;
    } catch {} 
    try {
      this.last_name = data.last_name ?? null;
    } catch {} 
    try {
      this.email = data.email ?? null;
    } catch {} 
    try {
      this.is_staff = data.is_staff ?? null;
    } catch {} 
    try {
      this.is_active = data.is_active ?? null;
    } catch {} 
    try {
      this.date_joined = data.date_joined ?? null;
    } catch {} 
    try {
      this.email_confirmed = data.email_confirmed ?? null;
    } catch {} 
    try {
    this.groups.setFilter({ user:  data.id });
    this.groups = data.groups || [];
    } catch {} 
    try {
    this.user_permissions.setFilter({ user:  data.id });
    this.user_permissions = data.user_permissions || [];
    } catch {} 
  }

  set logentry_set(value){
    this.setlogentry_set(value);
    this._updateForm('logentry_set');
  }

  set elnuser(value){
    this.setelnuser(value);
    this._updateForm('elnuser');
  }

  set shuttleinstance_set(value){
    this.setshuttleinstance_set(value);
    this._updateForm('shuttleinstance_set');
  }

  set id(value){
    this.setid(value);
    this._updateForm('id');
  }

  set password(value){
    this.setpassword(value);
    this._updateForm('password');
  }

  set last_login(value){
    this.setlast_login(value);
    this._updateForm('last_login');
  }

  set is_superuser(value){
    this.setis_superuser(value);
    this._updateForm('is_superuser');
  }

  set username(value){
    this.setusername(value);
    this._updateForm('username');
  }

  set first_name(value){
    this.setfirst_name(value);
    this._updateForm('first_name');
  }

  set last_name(value){
    this.setlast_name(value);
    this._updateForm('last_name');
  }

  set email(value){
    this.setemail(value);
    this._updateForm('email');
  }

  set is_staff(value){
    this.setis_staff(value);
    this._updateForm('is_staff');
  }

  set is_active(value){
    this.setis_active(value);
    this._updateForm('is_active');
  }

  set date_joined(value){
    this.setdate_joined(value);
    this._updateForm('date_joined');
  }

  set email_confirmed(value){
    this.setemail_confirmed(value);
    this._updateForm('email_confirmed');
  }

  set groups(value){
    this.setgroups(value);
    this._updateForm('groups');
  }

  set user_permissions(value){
    this.setuser_permissions(value);
    this._updateForm('user_permissions');
  }


  setlogentry_set(value){
    this.validate(value, SdcUser.fields.logentry_set);
    this._logentry_set.setIds(this.parseValue(value, SdcUser.fields.logentry_set));
  }

  setelnuser(value){
    this.validate(value, SdcUser.fields.elnuser);
    this._elnuser.setIds(this.parseValue(value, SdcUser.fields.elnuser));
  }

  setshuttleinstance_set(value){
    this.validate(value, SdcUser.fields.shuttleinstance_set);
    this._shuttleinstance_set.setIds(this.parseValue(value, SdcUser.fields.shuttleinstance_set));
  }

  setid(value){
    this.validate(value, SdcUser.fields.id);
    this._toManyFields.forEach(([x, fn]) => x.setFilter({[fn]: value}));
    this._id = this.parseValue(value, SdcUser.fields.id);
  }

  setpassword(value){
    this.validate(value, SdcUser.fields.password);
    this._password = this.parseValue(value, SdcUser.fields.password);
  }

  setlast_login(value){
    this.validate(value, SdcUser.fields.last_login);
    this._last_login = this.parseValue(value, SdcUser.fields.last_login);
  }

  setis_superuser(value){
    this.validate(value, SdcUser.fields.is_superuser);
    this._is_superuser = this.parseValue(value, SdcUser.fields.is_superuser);
  }

  setusername(value){
    this.validate(value, SdcUser.fields.username);
    this._username = this.parseValue(value, SdcUser.fields.username);
  }

  setfirst_name(value){
    this.validate(value, SdcUser.fields.first_name);
    this._first_name = this.parseValue(value, SdcUser.fields.first_name);
  }

  setlast_name(value){
    this.validate(value, SdcUser.fields.last_name);
    this._last_name = this.parseValue(value, SdcUser.fields.last_name);
  }

  setemail(value){
    this.validate(value, SdcUser.fields.email);
    this._email = this.parseValue(value, SdcUser.fields.email);
  }

  setis_staff(value){
    this.validate(value, SdcUser.fields.is_staff);
    this._is_staff = this.parseValue(value, SdcUser.fields.is_staff);
  }

  setis_active(value){
    this.validate(value, SdcUser.fields.is_active);
    this._is_active = this.parseValue(value, SdcUser.fields.is_active);
  }

  setdate_joined(value){
    this.validate(value, SdcUser.fields.date_joined);
    this._date_joined = this.parseValue(value, SdcUser.fields.date_joined);
  }

  setemail_confirmed(value){
    this.validate(value, SdcUser.fields.email_confirmed);
    this._email_confirmed = this.parseValue(value, SdcUser.fields.email_confirmed);
  }

  setgroups(value){
    this.validate(value, SdcUser.fields.groups);
    this._groups.setIds(this.parseValue(value, SdcUser.fields.groups));
  }

  setuser_permissions(value){
    this.validate(value, SdcUser.fields.user_permissions);
    this._user_permissions.setIds(this.parseValue(value, SdcUser.fields.user_permissions));
  }


  get logentry_set(){
    return this._logentry_set;
  }

  get elnuser(){
    return this._elnuser.length > 0 ? this._elnuser[0] : this._elnuser.new();
  }

  get shuttleinstance_set(){
    return this._shuttleinstance_set;
  }

  get id(){
    return this._id;
  }

  get password(){
    return this._password;
  }

  get last_login(){
    return this._last_login;
  }

  get is_superuser(){
    return this._is_superuser;
  }

  get username(){
    return this._username;
  }

  get first_name(){
    return this._first_name;
  }

  get last_name(){
    return this._last_name;
  }

  get email(){
    return this._email;
  }

  get is_staff(){
    return this._is_staff;
  }

  get is_active(){
    return this._is_active;
  }

  get date_joined(){
    return this._date_joined;
  }

  get email_confirmed(){
    return this._email_confirmed;
  }

  get groups(){
    return this._groups;
  }

  get user_permissions(){
    return this._user_permissions;
  }

}