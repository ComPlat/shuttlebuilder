import {AbstractSDC, app, trigger} from 'sdc_client';


/**
 * Form to link a new git repository or edit an existing `GitInstance`.
 *
 * - Arguments: `pk` (optional) is the id of the repo to edit; without it a new repo is created.
 * - New repo: "Save & Done" creates it and returns to `<git-instance-list>`. It is not active until activated there.
 * - Edit: there is no save button; changes are stored by the model form directly.
 * - The `name` cannot be changed after creation. Changing `url` or `branch` takes effect on the next reload/activation.
 * - Requires login.
 */
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