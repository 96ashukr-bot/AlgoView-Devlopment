import React, { useState } from 'react';
import { Card, CardBody, Col, Nav, NavItem, NavLink, Row, TabContent, TabPane } from 'reactstrap';
import { Hometxt, Messages, Profile, Settings, TabsVertical } from '../../../../../../Constant';
import { P } from '../../../../../../AbstractElements';
import HeaderCard from '../../../../../Common/Component/HeaderCard';

const Vertical = () => {
  const [VerticleTab, setVerticleTab] = useState('1');

  return (
    <Col sm='12' xl='6' className='xl-100 box-col-12'>
      <Card>
        <HeaderCard title={TabsVertical} />
        <CardBody>
          <Row>
            <Col sm='3' xs='12'>
              <Nav className='nav flex-column nav-pills'>
                <NavItem>
                  <NavLink href='#javascript' className={VerticleTab === '1' ? 'active' : ''} onClick={() => setVerticleTab('1')}>
                    {Hometxt}
                  </NavLink>
                </NavItem>
                <NavItem>
                  <NavLink href='#javascript' className={VerticleTab === '2' ? 'active' : ''} onClick={() => setVerticleTab('2')}>
                    {Profile}
                  </NavLink>
                </NavItem>
                <NavItem>
                  <NavLink href='#javascript' className={VerticleTab === '3' ? 'active' : ''} onClick={() => setVerticleTab('3')}>
                    {Messages}
                  </NavLink>
                </NavItem>
                <NavItem>
                  <NavLink href='#javascript' className={VerticleTab === '4' ? 'active' : ''} onClick={() => setVerticleTab('4')}>
                    {Settings}
                  </NavLink>
                </NavItem>
              </Nav>
            </Col>
            <Col sm='9' xs='12'>
              <TabContent activeTab={VerticleTab}>
                <TabPane className='fade show' tabId='1'>
                  <P>
                    {
                      'Button through front slim fit onesie bold zipper along the front elasticated cuffs piled detailing to the chest hood. Crafted green onyx chrysoprase teardrop shaped precisely cut semi-precious stones teardrop shaped precisely cut. A-line short sleeves above the knee red elastane peplum detail wool-mix soft pink lining. Sophisticated kymono-style neckline satin finish manly cloth check black and red precious. Khaki cotton blend military jacket flattering fit mock horn buttons and patch pockets showerproof black lightgrey.'
                    }
                  </P>
                </TabPane>
                <TabPane tabId='2'>
                  <P>
                    {
                      'Zipper along the front elasticated cuffs piled detailing to the chest hood. Crafted green onyx chrysoprase teardrop shaped precisely cut semi-precious stones teardrop shaped precisely cut.Button through front slim fit onesie bold  A-line short sleeves above the knee red elastane peplum detail wool-mix soft pink lining. Sophisticated kymono-style neckline satin finish manly cloth check black and red precious. Khaki cotton blend military jacket flattering fit mock horn buttons and patch pockets showerproof black lightgrey.'
                    }
                  </P>
                </TabPane>
                <TabPane tabId='3'>
                  <P>
                    {
                      'Above the along the front elasticated cuffs piled detailing to the chest hood. Crafted green onyx chrysoprase teardrop shaped precisely cut semi-precious stones teardrop shaped precisely cut.Button through front slim fit onesie bold  A-line short sleeves above the knee red elastane peplum detail wool-mix soft pink lining. Sophisticated kymono-style neckline satin finish manly cloth check black and red precious. Khaki cotton blend military jacket flattering fit mock horn buttons and patch pockets showerproof black lightgrey.'
                    }
                  </P>
                </TabPane>
                <TabPane tabId='4'>
                  <P>
                    {
                      'Neckline satin finish Above the along the front elasticated cuffs piled detailing to the chest hood. Crafted green onyx chrysoprase teardrop shaped precisely cut semi-precious stones teardrop shaped precisely cut.Button through front slim fit onesie bold  A-line short sleeves above the knee red elastane peplum detail wool-mix soft pink lining. Sophisticated kymono-style neckline satin finish manly cloth check black and red precious. Khaki cotton blend military jacket flattering fit mock horn buttons and patch pockets showerproof black lightgrey.'
                    }
                  </P>
                </TabPane>
              </TabContent>
            </Col>
          </Row>
        </CardBody>
      </Card>
    </Col>
  );
};

export default Vertical;
