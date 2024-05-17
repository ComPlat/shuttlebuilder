import {AbstractSDC, app, trigger} from 'sdc_client';


class GitInsatnceEditController extends AbstractSDC {

    constructor() {
        super();
        this.contentUrl = "/sdc_view/main_app/git_insatnce_edit"; //<git-insatnce-edit></git-insatnce-edit>
        this.model_name = 'GitInstance';

        /**
         * Events is an array of dom events.
         * The pattern is {'event': {'dom_selector': handler}}
         * Uncommend the following line to add events;
         */
        // this.events.unshift({'click': {'.header-sample': (ev, $elem)=> $elem.css('border', '2px solid black')}}});
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

    onInit() {}

    onLoad($html) {
        return super.onLoad($html);
    }

    willShow() {
        return super.willShow();
    }

    onRefresh() {
        return super.onRefresh();
    }

    form_header() {
        if(this.type === 'edit') {
            return 'Edit Link to Git Instance';
        }
        return 'Link new Git Instance';
    }

    form_btn() {
        if(this.type !== 'edit') {
            return <button className="btn btn-success">Save & Done</button>;
        }
        return '';
    }

    on_update() {
        if(this.type !== 'edit') {
            trigger('goTo', '..');
        }
    }
}

app.register(GitInsatnceEditController).addMixin('sdc-model-form');