import {AbstractSDC, app, trigger} from 'sdc_client';
import * as regexpTree from 'regexp-tree'

/**
 * Form to create, edit or copy a `ShuttleInstance` (the configuration of one Shuttle executable).
 *
 * - Arguments: `pk` (optional) is the id of the instance to edit; `copypk` (optional) prefills a new instance from an existing one, with ` (COPY)` added to the name.
 * - Without `pk`: "Save & Done" creates the instance (owned by the current user) and returns to `<shuttle-instance-list>`.
 * - With `pk`: there is no save button; changes are stored by the model form directly.
 * - The `common_name_parts` field is only shown for type `flat_tar`; it has a test input that shows the regex match and structure.
 * - The BagIt fields (`dst_bagit`, `user_bagit`, `passwort_bagit`, `profile`, `public_link`) are only shown when `with_converter` is checked.
 * - `host_key` is only shown for SFTP and `cert` only for WebDAV and ChemAssistent; `insecure` always shows a red warning (translated notes come from the template).
 * - For the transfer type `chemassistent` the `password` label becomes "API key (cam_...)", `user`, `host_key` and the converter block are hidden,
 *   and `dst` is pre-filled with the ChemAssistentManager URL (if configured) next to a link to create a job and an API key.
 *   For `win_i386` a hint says that Windows XP speaks at most TLS 1.2. Switching back restores the WebDAV/SFTP view.
 * - Shows the active git repo; if none is linked the form is not shown. Requires login.
 */
class ShuttleInstanceEditController extends AbstractSDC {

  constructor() {
    super();
    this.contentUrl = "/sdc_view/main_app/shuttle_instance_edit"; //<shuttle-instance-edit></shuttle-instance-edit>
    this.model_name = 'ShuttleInstance';
    this._regex_test_term = null;
    this._regex_term = null;
    this._is_init = false;
    this._saveOnChange = false;
    this.next = '..';

    /**
     * Events is an array of dom events.
     * The pattern is {'event': {'dom_selector': handler}}
     * Uncommend the following line to add events;
     */
    // 'input' (not 'change'): also fired by the AI assistant's fill_form, which avoids 'change' so model forms
    // do not save themselves. Browsers fire 'input' for selects and checkboxes as well.
    this.events.unshift({
      'input': {
        '#id_shuttle_type': this.onTypeChange,
        '#id_with_converter': this.onConverterChange,
        '#id_transfer': this.onTransferChange,
        '#id_architecture': this.onTransferChange,
        '#id_insecure': this.onInsecureChange
      }
    });
  }

  //-------------------------------------------------//
  // Lifecycle handler                               //
  // - onInit (tag parameter)                        //
  // - onLoad (DOM not set)                          //
  // - willShow  (DOM set)                           //
  // - onRefresh  (recalled on reload)              //
  //-------------------------------------------------//
  // - onRemove                                      //
  //-------------------------------------------------//

  get isAutoChange() {
    return true;
  }

  set isAutoChange(x) {
    this._saveOnChange = x;
    if (x) {
      this.next = null;
    }
  }

  async onLoad($html) {
    const {copypk} = this.params;
    if (copypk) {
      this._toCopy = await this._copy(copypk);
    }
    return super.onLoad($html);
  }

  willShow() {
    return super.willShow();
  }

  onRefresh() {
    let $typeSelect = this.find('#id_shuttle_type');
    if ($typeSelect.length > 0) {
      this.onTypeChange($typeSelect, null, true);
    }
    let $withConverter = this.find('#id_with_converter');
    if ($withConverter.length > 0) {
      this.onConverterChange($withConverter, null, true);
    }
    this._updateOptionFields(true);
    return super.onRefresh();
  }

  get regex_term() {
    if (!this._regex_term) {
      this._regex_term = this.find('#id_common_name_parts').val();
    }

    return this._regex_term;
  }

  get regex_test_term() {
    if (!this._regex_test_term) {
      this._regex_test_term = this.find('#testTextInput').val();
    }

    return this._regex_test_term;
  }

  form_header() {
    if (this.type === 'edit') {
      return 'Edit Shuttle Instance';
    }
    return 'New Shuttle Instance';
  }

  form_btn() {
    if (this.type !== 'edit') {
      return <button className="btn btn-success">Save & Done</button>;
    }
    return '';
  }

  render_help() {
    if (this._is_init) {
      return;
    }
    this._is_init = true;
    return <div className="regex-test-container">
      <label form="testTextInput" className="form-label">Test string:</label>
      <input type="text" className="timer-change form-control" id="testTextInput"
             aria-describedby="test text"
             value={this.regex_test_term}/>
      <this.render_help_result></this.render_help_result>

    </div>
  }

  render_help_result() {
    const regex_term = this.find('#id_common_name_parts').val();
    let ast = {};
    try {
      ast = regexpTree.parse(`/${regex_term}/`);
    } catch (e) {
      return <div className='alert alert-danger'>{e}</div>;
    }

    return <div className="container-fluid">
      <div className="row">
        <div className="col-5 re-result">
          {this.regex_test_res()}
        </div>
        <div className="col-7 re-tree">
          {this._parse_ast(ast.body)}
        </div>
      </div>
    </div>
  }

  regex_test_res() {
    const tester = regexpTree.optimize(`/${this.regex_term}/`).toRegExp();
    let res = tester.exec(this.regex_test_term);
    if (!res || !res.length) {
      return <p></p>;
    }
    if (res.length === 1) {
      return <p>{res[0]}</p>;
    }
    if (res.length >= 1) {
      return <ol>
        {res.slice(1).map(e => <li>{e}</li>)}
      </ol>;
    }
  }

  _parse_ast(ast) {
    if (!ast) {
      return <div className="regex-ast-entry">
        -
      </div>;
    }

    if (ast.type === "Disjunction") {
      return <div className="regex-ast-entry">
        {this._parse_ast(ast.left)}
        {this._parse_ast(ast.right)}
      </div>;
    }
    let text = ast.type;
    if (ast.symbol) {
      text += `: ${ast.symbol}`;
    } else if (ast.value) {
      text += `: ${ast.value}`;
    } else if (ast.kind) {
      let text_content = []
      if (ast.type === 'Assertion') {
        if (ast.negative) {
          text_content.push('negative');
        } else if (ast.kind === '^') {
          text_content.push('START');
        } else if (ast.kind === '$') {
          text_content.push('END');
        } else {
          text_content.push('positive');
        }
      }
      text_content.push(ast.kind);
      text += `: ${text_content.join(' ')}`;
    } else if (ast.number) {
      text += ` ${ast.number}`;
    }
    if (ast.from && ast.to && ast.from.symbol) {
      text += `: [${ast.from.symbol}-${ast.to.symbol}]`;
    } else if (ast.from && ast.to) {
      text += `: [${ast.from}-${ast.to}]`;
    }

    const rec_manager = (() => {
      let res = [];
      if (ast.assertion) {
        res.push(this._parse_ast(ast.assertion));
      }

      if (ast.expression) {
        res.push(this._parse_ast(ast.expression));
      }

      if (ast.expressions) {
        res = ast.expressions.map(expression => this._parse_ast(expression))
      }
      if (ast.quantifier) {
        res.push(this._parse_ast(ast.quantifier));
      }

      return <div>
        {res}
      </div>;
    })()
    return <div className="regex-ast-entry">
      <h4>{text}</h4>
      {rec_manager}
    </div>;
  }

  onTypeChange($dom, ev, fast) {
    const dur = fast ? 0 : 600;
    if ($dom.val() === 'flat_tar') {
      this.find('.id_common_name_parts').show(dur);
    } else {
      this.find('.id_common_name_parts').hide(dur);
    }
  }

  onTransferChange($dom, ev, fast) {
    this._updateOptionFields(fast);
  }

  onInsecureChange($dom, ev, fast) {
    this._updateOptionFields(fast);
  }

  /**
   * Show `host_key` only for SFTP, `cert` only for WebDAV and ChemAssistent, adapt the form for ChemAssistent
   * and attach the notes/warning (hidden in the template) to the fields.
   */
  _updateOptionFields(fast) {
    const dur = fast ? 0 : 300;
    const attach = (field, note) => {
      const $field = this.find(`.id_${field}`);
      const $note = this.find(`.option-note.${note}`);
      if ($field.length > 0 && $note.length > 0 && $field.find(`.option-note.${note}`).length === 0) {
        $field.append($note);
      }
    };
    attach('host_key', 'note-host-key');
    attach('cert', 'note-cert');
    attach('insecure', 'note-insecure');
    attach('dst', 'note-chemassistent-link');
    attach('architecture', 'note-xp-tls');

    const $transfer = this.find('#id_transfer');
    if ($transfer.length > 0) {
      const transfer = $transfer.val();
      const sftp = transfer === 'sftp';
      const cam = transfer === 'chemassistent';
      if (sftp) {
        this.find('.id_host_key').show(dur);
        this.find('.id_cert').hide(dur);
      } else {
        this.find('.id_host_key').hide(dur);
        this.find('.id_cert').show(dur);
      }
      this._updateChemAssistent(cam, fast, dur);
    }
    const $insecure = this.find('#id_insecure');
    if ($insecure.length > 0) {
      const checked = $insecure[0].checked;
      this.find('.option-note.note-insecure').toggleClass('fw-bold', checked);
      this.find('.id_insecure label').toggleClass('text-danger', checked);
    }
  }

  /**
   * ChemAssistent: `password` is the API key, no `user`, no `host_key`, no converter; link and TLS hint.
   */
  _updateChemAssistent(cam, fast, dur) {
    const $label = this.find('.id_password label');
    if ($label.length > 0) {
      if (cam) {
        if ($label.attr('data-orig-label') === undefined) {
          $label.attr('data-orig-label', $label.text());
        }
        const apiLabel = this.find('.option-note.note-api-key-label').text().trim();
        if (apiLabel) {
          $label.text(apiLabel);
        }
      } else if ($label.attr('data-orig-label') !== undefined) {
        $label.text($label.attr('data-orig-label'));
        $label.removeAttr('data-orig-label');
      }
    }
    const $withConverter = this.find('#id_with_converter');
    const convFields = ['dst_bagit', 'passwort_bagit', 'user_bagit', 'profile', 'public_link'];
    if (cam) {
      this.find('.id_user').hide(dur);
      this.find('.id_host_key').hide(dur);
      this.find('.id_with_converter').hide(dur);
      convFields.forEach(field => this.find(`.id_${field}`).hide(dur));
      // a hidden but checked box would make saving fail (the form rejects the converter for ChemAssistent)
      if ($withConverter.length > 0 && $withConverter[0].checked) {
        $withConverter[0].checked = false;
        if (!fast) {
          $withConverter[0].dispatchEvent(new Event('change', {bubbles: true}));
        }
      }
      const $dst = this.find('#id_dst');
      const url = this.find('.note-chemassistent-link a').attr('href');
      if ($dst.length > 0 && url && !$dst.val()) {
        $dst.val(url);
        if (!fast) {
          $dst[0].dispatchEvent(new Event('change', {bubbles: true}));
        }
      }
    } else {
      this.find('.id_user').show(dur);
      this.find('.id_with_converter').show(dur);
      if ($withConverter.length > 0) {
        this.onConverterChange($withConverter, null, true);
      }
    }
    this.find('.option-note.note-chemassistent-link').toggle(cam);
    const $arch = this.find('#id_architecture');
    const xp = cam && $arch.length > 0 && $arch.val() === 'win_i386';
    this.find('.option-note.note-xp-tls').toggle(xp);
  }

  onConverterChange($dom, ev, fast) {
    const convFields = ['dst_bagit', 'passwort_bagit', 'user_bagit', 'profile', 'public_link'];
    const dur = fast ? 0 : 600;
    const $transfer = this.find('#id_transfer');
    if ($transfer.length > 0 && $transfer.val() === 'chemassistent') {
      return;
    }
    if ($dom[0].checked) {
      convFields.forEach(field => {
        this.find(`.id_${field}`).show(dur);
      });
    } else {
      convFields.forEach(field => {
        this.find(`.id_${field}`).hide(dur);
      });
    }
  }

  onChange($elm) {
    if ($elm.attr('id') === 'id_common_name_parts') {
      this._regex_term = $elm.val();
      this.refresh();
      try {
        regexpTree.parse(`/${this._regex_term}/`);
      } catch (e) {
        return;
      }

    } else if ($elm.attr('id') === 'testTextInput') {
      this._regex_test_term = $elm.val();
      this.refresh();
      return;
    }

    if (this._saveOnChange) {
      this._mixins.SdcModelFormController.onChange.call(this, $elm);
    }
  }

  _onFormLoaded() {
    this.mixins.SdcModelFormController._onFormLoaded.call(this);
    if (this._toCopy) {
      Object.entries(this._toCopy).forEach(([key, value]) => {
        this.model.values[key] = value;
      });
      this.model.syncModelToForm();
    }
    this._updateOptionFields(true);

  }

  async _copy(pk) {
    const tempModel = this.newModel('ShuttleInstance', {pk: pk});
    await tempModel.load();
    const values = {...tempModel.values, pk: undefined}
    delete values.owner;
    values.name += ' (COPY)';
    return values;
  }
}

app.register(ShuttleInstanceEditController).addMixin('sdc-model-form');