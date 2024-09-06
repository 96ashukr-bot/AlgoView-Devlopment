import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import TabCardCommon from './tabCard';
import TabCardCommonClass from './TabsWithIcon';
import { Breadcrumbs } from '../../../../AbstractElements';
import ColorOptionClass from './ColorOption';
import ColorTabClass from './ColorTab';
import MaterialTabWithColorClass from './MaterialTabWithColor';

const TabCard = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle='Tabbed Card' parent="Bonus Ui" title="Tabbed Card" />
            <Container fluid={true}>
                <Row>
                    <TabCardCommon />
                    <TabCardCommonClass />
                    <ColorTabClass />
                    <ColorOptionClass />
                    <MaterialTabWithColorClass />
                </Row>
            </Container>
        </Fragment>
    );
};

export default TabCard;