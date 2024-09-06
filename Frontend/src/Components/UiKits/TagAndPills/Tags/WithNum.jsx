import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { Badges, H5 } from '../../../../AbstractElements';
import { TagsWithNumber } from '../../../../Constant';

const TagWithNum = () => {

  return (
    <Col sm="12" xl="6">
      <Card>
        <CardHeader>
          <H5>{TagsWithNumber}</H5>
        </CardHeader>
        <CardBody className="digits">
          <Badges attrBadge={{ color: 'primary', href: '#javascript' }}>{'1'}</Badges>
          <Badges attrBadge={{ color: 'secondary', href: '#javascript' }}  >{'2'}</Badges>
          <Badges attrBadge={{ color: 'success', href: '#javascript' }}  >{'3'}</Badges>
          <Badges attrBadge={{ color: 'info', href: '#javascript' }}  >{'4'}</Badges>
          <Badges attrBadge={{ color: 'warning', href: '#javascript' }}  >{'5'}</Badges>
          <Badges attrBadge={{ color: 'danger', href: '#javascript' }}  >{'6'}</Badges>
          <Badges attrBadge={{ color: 'light txt-dark', href: '#javascript' }}  >{'7'}</Badges>
          <Badges attrBadge={{ color: 'dark', href: '#javascript' }}  >{'8'}</Badges>
        </CardBody>
      </Card>
    </Col>
  );
};

export default TagWithNum;