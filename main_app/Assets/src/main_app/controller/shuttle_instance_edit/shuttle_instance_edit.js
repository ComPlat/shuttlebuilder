import {AbstractSDC, app, trigger} from 'sdc_client';


class ShuttleInstanceEditController extends AbstractSDC {

    constructor() {
        super();
        this.contentUrl = "/sdc_view/main_app/shuttle_instance_edit"; //<shuttle-instance-edit></shuttle-instance-edit>
        this.model_name = 'ShuttleInstance';

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
        console.log(this)
        let $typeSelect = this.find('#id_shuttle_type')
        if($typeSelect.length > 0){
            this.onTypeChange($typeSelect)
        }
        return super.onRefresh();
    }

    form_header() {
        if(this.type === 'edit') {
            return 'Edit Shuttle Instance';
        }
        return 'New Shuttle Instance';
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

    onTypeChange($dom) {
        if($dom.val() === 'flat_tar') {
            this.find('.id_common_prefix').show("slow");
        } else {
            this.find('.id_common_prefix').hide("slow");
        }
    }

}

app.register(ShuttleInstanceEditController).addMixin('sdc-model-form');