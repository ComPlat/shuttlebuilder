import {SdcModel, SdcQuerySet} from 'sdc_client';

export default class ElnUser extends SdcModel {


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
      "user": {
        "type": "OneToOneField",
        "required": true,
        "max_length": null,
        "is_relation": true,
        "many_to_many": false,
        "one_to_many": false,
        "many_to_one": false,
        "one_to_one": true,
        "related_model": "SdcUser",
        "remote_field": "elnuser"
      },
      "token": {
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
      "is_eln_user": {
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
      }
    }

  constructor(data = {}) {
    super("ElnUser");
    this._toManyFields = [];
    this._id = null;
    this._user = new SdcQuerySet('SdcUser');
    this._token = null;
    this._is_eln_user = null;
    this.setValues(data);
  }

  setValues(data = {}) {
    data.id ??= data.pk ?? null;
    try {
      this.id = data.id ?? null;
    } catch {} 
    try {
      if (data.user) { this.user = data.user; }
    } catch {} 
    try {
      this.token = data.token ?? null;
    } catch {} 
    try {
      this.is_eln_user = data.is_eln_user ?? null;
    } catch {} 
  }

  set id(value){
    this.setid(value);
    this._updateForm('id');
  }

  set user(value){
    this.setuser(value);
    this._updateForm('user');
  }

  set token(value){
    this.settoken(value);
    this._updateForm('token');
  }

  set is_eln_user(value){
    this.setis_eln_user(value);
    this._updateForm('is_eln_user');
  }


  setid(value){
    this.validate(value, ElnUser.fields.id);
    this._toManyFields.forEach(([x, fn]) => x.setFilter({[fn]: value}));
    this._id = this.parseValue(value, ElnUser.fields.id);
  }

  setuser(value){
    this.validate(value, ElnUser.fields.user);
    this._user.setIds(this.parseValue(value, ElnUser.fields.user));
  }

  settoken(value){
    this.validate(value, ElnUser.fields.token);
    this._token = this.parseValue(value, ElnUser.fields.token);
  }

  setis_eln_user(value){
    this.validate(value, ElnUser.fields.is_eln_user);
    this._is_eln_user = this.parseValue(value, ElnUser.fields.is_eln_user);
  }


  get id(){
    return this._id;
  }

  get user(){
    return this._user.length > 0 ? this._user[0] : this._user.new();
  }

  get token(){
    return this._token;
  }

  get is_eln_user(){
    return this._is_eln_user;
  }

}