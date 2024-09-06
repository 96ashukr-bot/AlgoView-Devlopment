import React, { Fragment } from 'react';
import DeniReactTreeView from 'deni-react-treeview';
import { Card, CardBody, Col } from 'reactstrap';
import HeaderCard from '../../Common/Component/HeaderCard';

const DragTree = () => {
    return (
        <Fragment>
            <Col sm="6">
                <Card>
                    <HeaderCard title="Lazy Loading Tree" />
                    <CardBody>
                        <div id="dragTree">
                            <DeniReactTreeView
                                url="https://raw.githubusercontent.com/denimar/deni-react-treeview/develop/src/assets/data/countries.json"
                                lazyLoad={true}
                            />
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default DragTree;