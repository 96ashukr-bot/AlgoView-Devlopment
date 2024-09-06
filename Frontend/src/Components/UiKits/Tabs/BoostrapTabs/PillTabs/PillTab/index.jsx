import React, { useState } from 'react';
import { Card, CardBody, Col, Nav, NavItem, NavLink, TabContent, TabPane } from 'reactstrap';
import { Contact, Hometxt, PillTabs, Profile } from '../../../../../../Constant';
import { P } from '../../../../../../AbstractElements';
import HeaderCard from '../../../../../Common/Component/HeaderCard';

const PillTab = () => {
  const [pillTab, setpillTab] = useState('1');

  return (
    <Col sm='12' xl='6' className='xl-100 box-col-12'>
      <Card>
        <HeaderCard title={PillTabs} />
        <CardBody>
          <Nav className='nav-pills'>
            <NavItem>
              <NavLink href='#javascript' className={pillTab === '1' ? 'active' : ''} onClick={() => setpillTab('1')}>
                {Hometxt}
              </NavLink>
            </NavItem>
            <NavItem>
              <NavLink href='#javascript' className={pillTab === '2' ? 'active' : ''} onClick={() => setpillTab('2')}>
                {Profile}
              </NavLink>
            </NavItem>
            <NavItem>
              <NavLink href='#javascript' className={pillTab === '3' ? 'active' : ''} onClick={() => setpillTab('3')}>
                {Contact}
              </NavLink>
            </NavItem>
          </Nav>
          <TabContent activeTab={pillTab}>
            <TabPane className='fade show' tabId='1'>
              <P attrPara={{ className: 'mb-0 m-t-30' }}>
                {
                  'Button through front slim fit onesie bold zipper along the front elasticated cuffs piled detailing to the chest hood. Crafted green onyx chrysoprase teardrop shaped precisely cut semi-precious stones A-line short sleeves above the knee red elastane peplum detail wool-mix soft pink lining. Sophisticated kymono-style neckline satin finish manly cloth check black and red precious. Khaki cotton blend military jacket flattering fit mock horn buttons and patch pockets showerproof black lightgrey.'
                }
              </P>
            </TabPane>
            <TabPane tabId='2'>
              <P attrPara={{ className: 'mb-0 m-t-30' }}>
                {
                  'Red precious through front slim fit onesie bold zipper along the front elasticated cuffs piled detailing to the chest hood. Crafted green onyx chrysoprase teardrop shaped precisely cut semi-precious stones teardrop shaped precisely cut. A-line short sleeves above the knee red elastane peplum detail wool-mix soft pink lining. Sophisticated kymono-style neckline satin finish manly cloth check black and red precious. Khaki cotton blend military jacket flattering fit mock horn buttons and patch pockets showerproof black lightgrey.'
                }
              </P>
            </TabPane>
            <TabPane tabId='3'>
              <P attrPara={{ className: 'mb-0 m-t-30' }}>
                {
                  'Stones teardrop front slim fit onesie bold zipper along the front elasticated cuffs piled detailing to the chest hood. Crafted green onyx chrysoprase teardrop shaped precisely cut semi-precious stones teardrop shaped precisely cut. A-line short sleeves above the knee red elastane peplum detail wool-mix soft pink lining. Sophisticated kymono-style neckline satin finish manly cloth check black and red precious. Khaki cotton blend military jacket flattering fit mock horn buttons and patch pockets showerproof black lightgrey., and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum'
                }
              </P>
            </TabPane>
          </TabContent>
        </CardBody>
      </Card>
    </Col>
  );
};

export default PillTab;
