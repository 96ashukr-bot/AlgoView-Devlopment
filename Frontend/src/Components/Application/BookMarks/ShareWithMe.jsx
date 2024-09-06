import React, { Fragment } from 'react';
import { Card, CardBody, Row } from 'reactstrap';
import { NoBookmarksFound, SharedWithMe } from '../../../Constant';
import GridClass from './Common/GridClass';

const SharedWithMee = () => {
    return (
        <Fragment>
            <Card className="mb-0">
                <GridClass title={SharedWithMe} />
                <CardBody>
                    <div className="details-bookmark text-center">
                        <Row></Row>
                        <div className="no-favourite">
                            <span>{NoBookmarksFound}</span>
                        </div>
                    </div>
                </CardBody>
            </Card>
        </Fragment>
    );
};
export default SharedWithMee;