import React, { Fragment } from 'react';
import HeaderCard from '../../Common/Component/HeaderCard';
import { Col, Card, CardBody } from 'reactstrap';
import dragula from 'react-dragula';
import { CopyDragNDrop } from '../../../Constant';

const Drag3 = () => {
    const dragulaDecoratorRight = (componentBackingInstance) => {
        if (componentBackingInstance) {
            let options = {
                copys: (el, source) => {
                    return el.id === 'left';
                },
                copyItem: (el, target, source, sibling) => {
                    return sibling.id === 'left';
                },
                accepts: (el, target, source, sibling) => {
                    return target.id === 'left';
                },
                copy: true,
                copySortSource: true,
                removeOnSpill: false,
                mirrorContainer: document.getElementById('right'),
            };
            dragula([componentBackingInstance], options);
        }
    };
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <HeaderCard title={CopyDragNDrop} />
                    <CardBody>
                        <div className="ui-sortable" id="draggableMultiple">
                            <div className='container' id="right" ref={dragulaDecoratorRight}>
                                <div>{'There\'s also the possibility of moving elements around in the same container, changing their position'}</div>
                                <div>{'This is the default use case. You only need to specify the containers you want to use'}</div>
                                <div>{'You can move these elements between these two containers'}</div>
                            </div>
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default Drag3;