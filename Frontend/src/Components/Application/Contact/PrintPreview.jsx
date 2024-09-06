import React, { Component } from 'react';
import { H5, H6, P } from '../../../AbstractElements';
class Printpreview extends Component {
  render() {
    const { selectedUser } = this.props
    return (
      <div className="profile-mail pt-0" id="DivIdToPrint">
        <div className="media"><img className="img-100 img-fluid m-r-20 rounded-circle" id="updateimg" src={selectedUser.avatar} alt="" />
          <div className="media-body mt-0">
            <H5><span id="printname">{selectedUser.name} </span><span id="printlast">{selectedUser.surname}</span></H5>
            <p id="printmail">{selectedUser.name}{"@gmail.com"}</p>
          </div>
        </div>
        <div className="email-general">
          <H6>{"General"}</H6>
          <P>{"Email Address"}: <span className="font-primary" id="mailadd">{selectedUser.name}{"@gmail.com"}   </span></P>
        </div>
      </div>
    );
  }
}

export default Printpreview