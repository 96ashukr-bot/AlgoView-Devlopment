import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../../AbstractElements';
import BasicTabCard from '../BoostrapTabs/BasicTabCard';
import BottomLeftAlignCard from '../BoostrapTabs/TabAligns/BottomLeftAlignCard';
import RighhtAlign from '../BoostrapTabs/TabAligns/RightAlign';
import WithIcon from '../BoostrapTabs/WithIcon';
import Vertical from '../BoostrapTabs/TabAligns/Vertical';
import PillTab from '../BoostrapTabs/PillTabs/PillTab';
import PillTabWithIcon from '../BoostrapTabs/PillTabs/PillTabWithIcon';
import PillDarkTab from '../BoostrapTabs/PillTabs/PillTabColor/Dark';
import PillPrimaryTab from '../BoostrapTabs/PillTabs/PillTabColor/Primary';
import PillSecondaryTab from '../BoostrapTabs/PillTabs/PillTabColor/Secondary';
import PillSucessTab from '../BoostrapTabs/PillTabs/PillTabColor/Success';
import PillInfoTab from '../BoostrapTabs/PillTabs/PillTabColor/Info';
import PillWarningTab from '../BoostrapTabs/PillTabs/PillTabColor/Warning';
import PillDangerTab from '../BoostrapTabs/PillTabs/PillTabColor/Danger';

const TabBootstrap = (props) => {

  return (
    <Fragment>
      <Breadcrumbs mainTitle="Bootstrap Tabs" parent="Ui Kits" title="Bootstrap Tabs" />
      <Container fluid={true}>
        <Row>
          <BasicTabCard />
          <BottomLeftAlignCard />
          <WithIcon />
          <RighhtAlign />
          <Vertical />
          <PillTab />
          <PillTabWithIcon />
          <PillDarkTab />
          <PillPrimaryTab />
          <PillSecondaryTab />
          <PillSucessTab />
          <PillInfoTab />
          <PillWarningTab />
          <PillDangerTab />
        </Row>
      </Container>
    </Fragment>
  );
};

export default TabBootstrap;