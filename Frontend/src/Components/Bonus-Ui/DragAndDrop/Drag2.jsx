import React, { Fragment } from 'react';
import HeaderCard from '../../Common/Component/HeaderCard';
import { Col, Card, CardBody } from 'reactstrap';
import dragula from 'react-dragula';
import { SpillDragNDrop } from '../../../Constant';

const Drag2 = () => {
    const dragulaDecoratorSpill = (componentBackingInstance) => {
        if (componentBackingInstance) {
            let options = {
                isContainer: function (el) {
                    return false;
                },
                moves: function (el, source, handle, sibling) {
                    return true;
                },
                accepts: function (el, target, source, sibling) {
                    return true;
                },
                invalid: function (el, handle) {
                    return false;
                },
                direction: 'vertical',
                copy: false,
                copySortSource: false,
                revertOnSpill: true,
                removeOnSpill: true,
                mirrorContainer: document.body,
                ignoreInputTextSelection: true
            };
            dragula([componentBackingInstance], options);
        }
    };
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <HeaderCard title={SpillDragNDrop} />
                    <CardBody>
                        <div className="ui-sortable" id="draggableMultiple">
                            <div className='container' ref={dragulaDecoratorSpill}>
                                <div>{'You can move these elements between these two containers'}</div>
                                <div>{'Moving them anywhere else isn\'t quite possible'}</div>
                                <div>{'There\'s also the possibility of moving elements around in the same container, changing their position'}</div>
                                <div>{'This is the default use case. You only need to specify the containers you want to use'}</div>
                                <div>{'You can move these elements between these two containers'}</div>
                                <div>{'Moving them anywhere else isn\'t quite possible'}</div>
                                <div>{'Make sure to check out the documentation on GitHub!'}</div>
                            </div>
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default Drag2;