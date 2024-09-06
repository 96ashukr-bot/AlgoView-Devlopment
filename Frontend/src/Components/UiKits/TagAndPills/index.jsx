import React, { Fragment } from 'react';
import { Container,Row } from 'reactstrap';
import ContextualBadge from './Tags/Contextual';
import ContextualPills from './Pills/Contextual';
import TagWithNum from './Tags/WithNum';
import PillWithNum from './Pills/WithNum';
import TagWithIcon from './Tags/WithIcon';
import PillWithIcon from './Pills/WithIcon';
import { Breadcrumbs } from '../../../AbstractElements';
import BadgeExample from './BadgeExample';
import ButtonPart from './ButtonPart';

const TagAndPills = () => {
    return (
      <Fragment>
        <Breadcrumbs mainTitle="Tag & Pills" parent="Ui Kits" title="Tag & Pills"/>
        <Container fluid={true}>
          <Row>
            <ContextualBadge />
            <ContextualPills />
            <TagWithNum />
            <PillWithNum />
            <TagWithIcon />
            <PillWithIcon />
            <BadgeExample />
            <ButtonPart />
          </Row>
        </Container>
      </Fragment>
    );
};

export default TagAndPills;