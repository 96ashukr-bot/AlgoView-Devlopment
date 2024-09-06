import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H5, P } from '../../../../AbstractElements';

const InlineTextCard = () =>{
    return(
      <Col sm="12" xl="6">
        <Card>
          <CardHeader>
            <H5>{'Inline text elements'}</H5><span>{'Styling for common inline HTML5 elements.'}</span>
          </CardHeader>
          <CardBody>
            <P>{'You can use the mark tag to'}
              <mark>{'highlight'}</mark> {'text.'}
            </P>
            <P>
              <del>{'This line of text is meant to be treated as deleted text.'}</del>
            </P>
            <P>
              <s>{'This line of text is meant to be treated as no longer accurate.'}</s>
            </P>
            <P><ins>{'This line of text is meant to be treated as an addition to the document.'}</ins></P>
            <P>
              <u>{'This line of text will render as underlined'}</u>
            </P>
            <P><small>{'This line of text is meant to be treated as fine print.'}</small></P>
            <P><strong>{'This line rendered as bold text.'}</strong></P>
            <P><em>{'This line rendered as italicized text.'}</em></P>
          </CardBody>
        </Card>
      </Col>
    );
};

export default InlineTextCard;