import React, { Fragment } from 'react';
import HeaderCard from '../../Common/Component/HeaderCard';
import { Col, Card, CardBody } from 'reactstrap';
import dragula from 'react-dragula';
import { ClickAndDrag } from '../../../Constant';

const Drag1 = () => {
    const dragulaDecorator = (componentBackingInstance) => {
        if (componentBackingInstance) {
            let options = {};
            dragula([componentBackingInstance], options);
        }
    };
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <HeaderCard title={ClickAndDrag} />
                    <CardBody>
                        <div className="ui-sortable small-drag" id="draggableMultiple">
                            <div className='container' ref={dragulaDecorator}>
                                <div>{'You can move these elements between these two containers'}</div>
                                <div>{'Moving them anywhere else isn\'t quite possible'}</div>
                                <div>{'There\'s also the possibility of moving elements around in the same container, changing their position'}</div>
                                <div>{'This is the default use case. You only need to specify the containers you want to use'}</div>
                                <div>{'More interactive use cases lie ahead'}</div>
                                <div>{'Make sure to check out the documentation on GitHub!'}</div>
                            </div>
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default Drag1;