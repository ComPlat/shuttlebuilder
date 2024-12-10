import {AbstractSDC, app, trigger} from 'sdc_client';
import * as regexpTree from 'regexp-tree'

class ShuttleInstanceEditController extends AbstractSDC {

    constructor() {
        super();
        this.contentUrl = "/sdc_view/main_app/shuttle_instance_edit"; //<shuttle-instance-edit></shuttle-instance-edit>
        this.model_name = 'ShuttleInstance';
        this._regex_test_term = null;
        this._regex_term = null;
        this._is_init = false;

        /**
         * Events is an array of dom events.
         * The pattern is {'event': {'dom_selector': handler}}
         * Uncommend the following line to add events;
         */
        this.events.unshift({'change': {'#id_shuttle_type': this.onTypeChange}});
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

    onInit() {
    }

    onLoad($html) {
        return super.onLoad($html);
    }

    willShow() {
        return super.willShow();
    }

    onRefresh() {
        let $typeSelect = this.find('#id_shuttle_type');
        if ($typeSelect.length > 0) {
            this.onTypeChange($typeSelect);
        }
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

    on_update() {
        if (this.type !== 'edit') {
            trigger('goTo', '..');
        }
    }

    render_help() {
        if(this._is_init) {
            return;
        }
        this._is_init = true;
        return <div className="regex-test-container">
            <label form="testTextInput" className="form-label">Test string:</label>
            <input type="email" className="timer-change form-control" id="testTextInput"
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

    onTypeChange($dom) {
        if ($dom.val() === 'flat_tar') {
            this.find('.id_common_name_parts').show("slow");
        } else {
            this.find('.id_common_name_parts').hide("slow");
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

        this._mixins.SdcModelFormController.onChange.call(this, $elm);
    }
}

app.register(ShuttleInstanceEditController).addMixin('sdc-model-form');