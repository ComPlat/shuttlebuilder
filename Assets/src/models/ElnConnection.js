import {SdcModel, SdcQuerySet} from 'sdc_client';

export default class ElnConnection extends SdcModel {


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
      "url": {
        "type": "CharField",
        "required": true,
        "max_length": 200,
        "is_relation": false,
        "many_to_many": null,
        "one_to_many": null,
        "many_to_one": null,
        "one_to_one": null,
        "related_model": null,
        "remote_field": null
      },
      "active": {
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
      "token": {
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
      "device": {
        "type": "IntegerField",
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
    super("ElnConnection");
    this._toManyFields = [];
    this._id = null;
    this._url = null;
    this._active = null;
    this._token = null;
    this._device = null;
    this.setValues(data);
  }

  setValues(data = {}) {
    data.id ??= data.pk ?? null;
    try {
      this.id = data.id ?? null;
    } catch {} 
    try {
      this.url = data.url ?? null;
    } catch {} 
    try {
      this.active = data.active ?? null;
    } catch {} 
    try {
      this.token = data.token ?? null;
    } catch {} 
    try {
      this.device = data.device ?? null;
    } catch {} 
  }

  set id(value){
    this.setid(value);
    this._updateForm('id');
  }

  set url(value){
    this.seturl(value);
    this._updateForm('url');
  }

  set active(value){
    this.setactive(value);
    this._updateForm('active');
  }

  set token(value){
    this.settoken(value);
    this._updateForm('token');
  }

  set device(value){
    this.setdevice(value);
    this._updateForm('device');
  }


  setid(value){
    this.validate(value, ElnConnection.fields.id);
    this._toManyFields.forEach(([x, fn]) => x.setFilter({[fn]: value}));
    this._id = this.parseValue(value, ElnConnection.fields.id);
  }

  seturl(value){
    this.validate(value, ElnConnection.fields.url);
    this._url = this.parseValue(value, ElnConnection.fields.url);
  }

  setactive(value){
    this.validate(value, ElnConnection.fields.active);
    this._active = this.parseValue(value, ElnConnection.fields.active);
  }

  settoken(value){
    this.validate(value, ElnConnection.fields.token);
    this._token = this.parseValue(value, ElnConnection.fields.token);
  }

  setdevice(value){
    this.validate(value, ElnConnection.fields.device);
    this._device = this.parseValue(value, ElnConnection.fields.device);
  }


  get id(){
    return this._id;
  }

  get url(){
    return this._url;
  }

  get active(){
    return this._active;
  }

  get token(){
    return this._token;
  }

  get device(){
    return this._device;
  }

}