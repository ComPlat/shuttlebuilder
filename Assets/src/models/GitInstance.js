import {SdcModel, SdcQuerySet} from 'sdc_client';

export default class GitInstance extends SdcModel {


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
      "url": {
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
      "branch": {
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
      "last_reload": {
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
      }
    }

  constructor(data = {}) {
    super("GitInstance");
    this._toManyFields = [];
    this._id = null;
    this._name = null;
    this._url = null;
    this._branch = null;
    this._is_active = null;
    this._last_reload = null;
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
      this.url = data.url ?? null;
    } catch {} 
    try {
      this.branch = data.branch ?? null;
    } catch {} 
    try {
      this.is_active = data.is_active ?? null;
    } catch {} 
    try {
      this.last_reload = data.last_reload ?? null;
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

  set url(value){
    this.seturl(value);
    this._updateForm('url');
  }

  set branch(value){
    this.setbranch(value);
    this._updateForm('branch');
  }

  set is_active(value){
    this.setis_active(value);
    this._updateForm('is_active');
  }

  set last_reload(value){
    this.setlast_reload(value);
    this._updateForm('last_reload');
  }


  setid(value){
    this.validate(value, GitInstance.fields.id);
    this._toManyFields.forEach(([x, fn]) => x.setFilter({[fn]: value}));
    this._id = this.parseValue(value, GitInstance.fields.id);
  }

  setname(value){
    this.validate(value, GitInstance.fields.name);
    this._name = this.parseValue(value, GitInstance.fields.name);
  }

  seturl(value){
    this.validate(value, GitInstance.fields.url);
    this._url = this.parseValue(value, GitInstance.fields.url);
  }

  setbranch(value){
    this.validate(value, GitInstance.fields.branch);
    this._branch = this.parseValue(value, GitInstance.fields.branch);
  }

  setis_active(value){
    this.validate(value, GitInstance.fields.is_active);
    this._is_active = this.parseValue(value, GitInstance.fields.is_active);
  }

  setlast_reload(value){
    this.validate(value, GitInstance.fields.last_reload);
    this._last_reload = this.parseValue(value, GitInstance.fields.last_reload);
  }


  get id(){
    return this._id;
  }

  get name(){
    return this._name;
  }

  get url(){
    return this._url;
  }

  get branch(){
    return this._branch;
  }

  get is_active(){
    return this._is_active;
  }

  get last_reload(){
    return this._last_reload;
  }

}