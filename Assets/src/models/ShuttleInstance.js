import {SdcModel, SdcQuerySet} from 'sdc_client';

export default class ShuttleInstance extends SdcModel {


  static fields = {
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
      "name": {
        "type": "CharField",
        "required": true,
        "max_length": 50,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "user": {
        "type": "CharField",
        "required": true,
        "max_length": 50,
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
        "max_length": 100,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "transfer": {
        "type": "CharField",
        "required": true,
        "max_length": 255,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "src": {
        "type": "CharField",
        "required": true,
        "max_length": 255,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "dst": {
        "type": "CharField",
        "required": true,
        "max_length": 255,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "shuttle_type": {
        "type": "CharField",
        "required": true,
        "max_length": 255,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "common_name_parts": {
        "type": "CharField",
        "required": false,
        "max_length": 255,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "duration": {
        "type": "PositiveIntegerField",
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
      "architecture": {
        "type": "CharField",
        "required": true,
        "max_length": 255,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "with_converter": {
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
      "user_bagit": {
        "type": "CharField",
        "required": false,
        "max_length": 50,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "passwort_bagit": {
        "type": "CharField",
        "required": false,
        "max_length": 100,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "dst_bagit": {
        "type": "CharField",
        "required": false,
        "max_length": 255,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "public_link": {
        "type": "CharField",
        "required": false,
        "max_length": 200,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "profile": {
        "type": "FileField",
        "required": false,
        "max_length": 100,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null,
        "max_size": 5368709120,
        "allowed_types": null
      },
      "last_update": {
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
      "last_build": {
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
      "owner": {
        "type": "ForeignKey",
        "required": false,
        "max_length": null,
        "is_relation": true,
        "many_to_many": false,
        "one_to_many": false,
        "many_to_one": true,
        "one_to_one": false,
        "related_model": "SdcUser",
        "remote_field": "shuttleinstance"
      }
    }

  constructor(data = {}) {
    super("ShuttleInstance");
    this._toManyFields = [];
    this._id = null;
    this._name = null;
    this._user = null;
    this._password = null;
    this._transfer = null;
    this._src = null;
    this._dst = null;
    this._shuttle_type = null;
    this._common_name_parts = null;
    this._duration = null;
    this._architecture = null;
    this._with_converter = null;
    this._user_bagit = null;
    this._passwort_bagit = null;
    this._dst_bagit = null;
    this._public_link = null;
    this._profile = null;
    this._last_update = null;
    this._last_build = null;
    this._owner = new SdcQuerySet('SdcUser');
    this.setValues(data);
  }

  setValues(data = {}) {
    data.id ??= data.pk ?? null;
    try {
      this.id = data.id ?? null;
    } catch {} 
    try {
      this.name = data.name ?? null;
    } catch {} 
    try {
      this.user = data.user ?? null;
    } catch {} 
    try {
      this.password = data.password ?? null;
    } catch {} 
    try {
      this.transfer = data.transfer ?? null;
    } catch {} 
    try {
      this.src = data.src ?? null;
    } catch {} 
    try {
      this.dst = data.dst ?? null;
    } catch {} 
    try {
      this.shuttle_type = data.shuttle_type ?? null;
    } catch {} 
    try {
      this.common_name_parts = data.common_name_parts ?? null;
    } catch {} 
    try {
      this.duration = data.duration ?? null;
    } catch {} 
    try {
      this.architecture = data.architecture ?? null;
    } catch {} 
    try {
      this.with_converter = data.with_converter ?? null;
    } catch {} 
    try {
      this.user_bagit = data.user_bagit ?? null;
    } catch {} 
    try {
      this.passwort_bagit = data.passwort_bagit ?? null;
    } catch {} 
    try {
      this.dst_bagit = data.dst_bagit ?? null;
    } catch {} 
    try {
      this.public_link = data.public_link ?? null;
    } catch {} 
    try {
      this.profile = data.profile ?? null;
    } catch {} 
    try {
      this.last_update = data.last_update ?? null;
    } catch {} 
    try {
      this.last_build = data.last_build ?? null;
    } catch {} 
    try {
      if (data.owner) { this.owner = data.owner; }
    } catch {} 
  }

  set id(value){
    this.setid(value);
    this._updateForm('id');
  }

  set name(value){
    this.setname(value);
    this._updateForm('name');
  }

  set user(value){
    this.setuser(value);
    this._updateForm('user');
  }

  set password(value){
    this.setpassword(value);
    this._updateForm('password');
  }

  set transfer(value){
    this.settransfer(value);
    this._updateForm('transfer');
  }

  set src(value){
    this.setsrc(value);
    this._updateForm('src');
  }

  set dst(value){
    this.setdst(value);
    this._updateForm('dst');
  }

  set shuttle_type(value){
    this.setshuttle_type(value);
    this._updateForm('shuttle_type');
  }

  set common_name_parts(value){
    this.setcommon_name_parts(value);
    this._updateForm('common_name_parts');
  }

  set duration(value){
    this.setduration(value);
    this._updateForm('duration');
  }

  set architecture(value){
    this.setarchitecture(value);
    this._updateForm('architecture');
  }

  set with_converter(value){
    this.setwith_converter(value);
    this._updateForm('with_converter');
  }

  set user_bagit(value){
    this.setuser_bagit(value);
    this._updateForm('user_bagit');
  }

  set passwort_bagit(value){
    this.setpasswort_bagit(value);
    this._updateForm('passwort_bagit');
  }

  set dst_bagit(value){
    this.setdst_bagit(value);
    this._updateForm('dst_bagit');
  }

  set public_link(value){
    this.setpublic_link(value);
    this._updateForm('public_link');
  }

  set profile(value){
    this.setprofile(value);
    this._updateForm('profile');
  }

  set last_update(value){
    this.setlast_update(value);
    this._updateForm('last_update');
  }

  set last_build(value){
    this.setlast_build(value);
    this._updateForm('last_build');
  }

  set owner(value){
    this.setowner(value);
    this._updateForm('owner');
  }


  setid(value){
    this.validate(value, ShuttleInstance.fields.id);
    this._toManyFields.forEach(([x, fn]) => x.setFilter({[fn]: value}));
    this._id = this.parseValue(value, ShuttleInstance.fields.id);
  }

  setname(value){
    this.validate(value, ShuttleInstance.fields.name);
    this._name = this.parseValue(value, ShuttleInstance.fields.name);
  }

  setuser(value){
    this.validate(value, ShuttleInstance.fields.user);
    this._user = this.parseValue(value, ShuttleInstance.fields.user);
  }

  setpassword(value){
    this.validate(value, ShuttleInstance.fields.password);
    this._password = this.parseValue(value, ShuttleInstance.fields.password);
  }

  settransfer(value){
    this.validate(value, ShuttleInstance.fields.transfer);
    this._transfer = this.parseValue(value, ShuttleInstance.fields.transfer);
  }

  setsrc(value){
    this.validate(value, ShuttleInstance.fields.src);
    this._src = this.parseValue(value, ShuttleInstance.fields.src);
  }

  setdst(value){
    this.validate(value, ShuttleInstance.fields.dst);
    this._dst = this.parseValue(value, ShuttleInstance.fields.dst);
  }

  setshuttle_type(value){
    this.validate(value, ShuttleInstance.fields.shuttle_type);
    this._shuttle_type = this.parseValue(value, ShuttleInstance.fields.shuttle_type);
  }

  setcommon_name_parts(value){
    this.validate(value, ShuttleInstance.fields.common_name_parts);
    this._common_name_parts = this.parseValue(value, ShuttleInstance.fields.common_name_parts);
  }

  setduration(value){
    this.validate(value, ShuttleInstance.fields.duration);
    this._duration = this.parseValue(value, ShuttleInstance.fields.duration);
  }

  setarchitecture(value){
    this.validate(value, ShuttleInstance.fields.architecture);
    this._architecture = this.parseValue(value, ShuttleInstance.fields.architecture);
  }

  setwith_converter(value){
    this.validate(value, ShuttleInstance.fields.with_converter);
    this._with_converter = this.parseValue(value, ShuttleInstance.fields.with_converter);
  }

  setuser_bagit(value){
    this.validate(value, ShuttleInstance.fields.user_bagit);
    this._user_bagit = this.parseValue(value, ShuttleInstance.fields.user_bagit);
  }

  setpasswort_bagit(value){
    this.validate(value, ShuttleInstance.fields.passwort_bagit);
    this._passwort_bagit = this.parseValue(value, ShuttleInstance.fields.passwort_bagit);
  }

  setdst_bagit(value){
    this.validate(value, ShuttleInstance.fields.dst_bagit);
    this._dst_bagit = this.parseValue(value, ShuttleInstance.fields.dst_bagit);
  }

  setpublic_link(value){
    this.validate(value, ShuttleInstance.fields.public_link);
    this._public_link = this.parseValue(value, ShuttleInstance.fields.public_link);
  }

  setprofile(value){
    this.validate(value, ShuttleInstance.fields.profile);
    this._profile = this.parseValue(value, ShuttleInstance.fields.profile);
  }

  setlast_update(value){
    this.validate(value, ShuttleInstance.fields.last_update);
    this._last_update = this.parseValue(value, ShuttleInstance.fields.last_update);
  }

  setlast_build(value){
    this.validate(value, ShuttleInstance.fields.last_build);
    this._last_build = this.parseValue(value, ShuttleInstance.fields.last_build);
  }

  setowner(value){
    this.validate(value, ShuttleInstance.fields.owner);
    this._owner.setIds(this.parseValue(value, ShuttleInstance.fields.owner));
  }


  get id(){
    return this._id;
  }

  get name(){
    return this._name;
  }

  get user(){
    return this._user;
  }

  get password(){
    return this._password;
  }

  get transfer(){
    return this._transfer;
  }

  get src(){
    return this._src;
  }

  get dst(){
    return this._dst;
  }

  get shuttle_type(){
    return this._shuttle_type;
  }

  get common_name_parts(){
    return this._common_name_parts;
  }

  get duration(){
    return this._duration;
  }

  get architecture(){
    return this._architecture;
  }

  get with_converter(){
    return this._with_converter;
  }

  get user_bagit(){
    return this._user_bagit;
  }

  get passwort_bagit(){
    return this._passwort_bagit;
  }

  get dst_bagit(){
    return this._dst_bagit;
  }

  get public_link(){
    return this._public_link;
  }

  get profile(){
    return this._profile;
  }

  get last_update(){
    return this._last_update;
  }

  get last_build(){
    return this._last_build;
  }

  get owner(){
    return this._owner.length > 0 ? this._owner[0] : this._owner.new();
  }

}