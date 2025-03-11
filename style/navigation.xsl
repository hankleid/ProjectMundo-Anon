<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <xsl:template name="navbar">
        <div class="topnav">
          <a class="active" href="index.xml">Project Mundo</a>
          <button class="dropbtn" onclick="dropDown()">Dropdown
            <i class="fa fa-caret-down"></i>
          </button>
          <div class="dropdown-content" id="lang-dropdown">
            <!-- dropdown links will be dynamically generated -->
            <a href="#" id="spa">Link 1</a>
          </div>
          <a href="index.xml">About</a>
        </div>
    </xsl:template>

</xsl:transform>