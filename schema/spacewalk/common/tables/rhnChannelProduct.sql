--
-- Copyright (c) 2008 Red Hat, Inc.
--
-- This software is licensed to you under the GNU General Public License,
-- version 2 (GPLv2). There is NO WARRANTY for this software, express or
-- implied, including the implied warranties of MERCHANTABILITY or FITNESS
-- FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
-- along with this software; if not, see
-- http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
-- 
-- Red Hat trademarks are not licensed under GPLv2. No permission is
-- granted to use or replicate Red Hat trademarks that are incorporated
-- in this software or its documentation. 
--


CREATE TABLE rhnChannelProduct
(
    id        NUMBER NOT NULL 
                  CONSTRAINT rhn_channelprod_id_pk PRIMARY KEY 
                  USING INDEX TABLESPACE [[64k_tbs]], 
    product   VARCHAR2(256) NOT NULL, 
    version   VARCHAR2(64) NOT NULL, 
    beta      CHAR(1) 
                  DEFAULT ('N') NOT NULL 
                  CONSTRAINT rhn_channelprod_beta_ck
                      CHECK (beta in ( 'Y' , 'N' )), 
    created   DATE 
                  DEFAULT (sysdate) NOT NULL, 
    modified  DATE 
                  DEFAULT (sysdate) NOT NULL
)
ENABLE ROW MOVEMENT
;

CREATE UNIQUE INDEX rhn_channelprod_p_v_b_uq
    ON rhnChannelProduct (product, version, beta)
    TABLESPACE [[64k_tbs]];

CREATE SEQUENCE rhn_channelprod_id_seq;

