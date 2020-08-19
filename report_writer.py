class Report:
    __file = None
    __id = 0
    __script = """<script>
        var elems = document.getElementsByClassName('idx');
        var idx_space = document.getElementsByClassName('idx-space');
        var current_open_el = 0
        for(var i = 0; i < elems.length; ++i) {
            elems[i].addEventListener('click', function(event) {
                var el = event.path[0]
                var open_data = el.getAttribute("open-data")
                var open_el = document.getElementById(open_data)
                if(current_open_el) {
                    var current_open_el_id = current_open_el.getAttribute('id')
                    if(open_data != current_open_el_id) {
                        current_open_el.setAttribute('class', 'cloud')
                    }
                }
                if(open_el.getAttribute('class') == 'cloud') {
                    open_el.setAttribute('class', 'cloud show')
                    current_open_el = open_el
                } else {
                    open_el.setAttribute('class', 'cloud')
                }
            })
        }
        var w = document.getElementsByClassName('sv_dateime_inf')[0].clientWidth;
        for(var i = 0; i < idx_space.length; ++i) {
            idx_space[i].style.width = w + 'px';
        }
    </script>"""
    __end_body = ''

    def __init__(self, filename='report.html'):
        self.__file = open(filename, 'w')
        self.__begin()
    
    def __del__(self):
        self.__endbody()
        self.__end()
        self.__file.close()
    
    def write_coefs(self, sv, datetime, coefs):
        self.__file.write('<span class="sv_dateime_inf">')
        self.__file.write(sv + ' ')
        self.__file.write(datetime.strftime("%Y %m %d %H %M %S") + ' ')
        self.__file.write('</span>')
        coef_indexes_q = len(coefs)
        for coef_idx in coefs:
            right = coefs[coef_idx]['rigth_coef']
            errors = coefs[coef_idx]['error_coefs']

            errors_length = len(errors)

            color = 'red'
            if(errors_length == 0):
                color = 'green'
            
            self.__file.write('<span class="idx" open-data="{0}" style="color:{1}">'.format(self.__id, color))
            self.__file.write(right['value'].replace(' ', '&nbsp;'))
            self.__file.write('</span>')

            self.__file.write('<span class="cloud" id="{0}">'.format(self.__id))
            self.__id += 1
            self.__file.write('found in files({0}):<br>'.format(right['count']))

            self.__file.write('<ol>')
            for owner in right['owners']:
                self.__file.write('<li>{0}</li>'.format(owner))
            self.__file.write('</ol>')

            if(errors_length > 0):
                self.__file.write('errors({0}):<br>'.format(len(errors)))
                self.__file.write('<ol>')
                for error in errors:
                    self.__file.write('<li>')
                    self.__file.write(self.__highlight_differense(right['value'].replace(' ', '&nbsp;'), error['value'].replace(' ', '&nbsp;')) + '<br>')

                    self.__file.write('<ol>found in files({0}):'.format(len(error['owners'])))
                    for owner in error['owners']:
                        self.__file.write('<li>{0}</li>'.format(owner))
                    self.__file.write('</ol></li>')
                
                self.__file.write('</ol>')

            self.__file.write('</span>')

            if(coef_idx == 2 or ((coef_idx - 2) % 4 == 0 and coef_idx != (coef_indexes_q - 1))):
                self.__file.write('<br><span class="idx-space"></span>')
        
        self.__file.write('<br>')
        
    def __highlight_differense(self, val1, val2):
        val1_len = len(val1)
        val2_len = len(val2)
        min_v = min([val1_len, val2_len])
        ret = ''
        for i in range(min_v):
            if (val1[i] == val2[i]):
                ret += val2[i]
            else:
                ret += '<span style="color: yellow">{0}</span>'.format(val2[i])

        return ret

    def __endbody(self):
        self.__file.write(self.__end_body)
        self.__file.write(self.__script + '</body>')

    def add_end_body(self, str_end):
        self.__end_body += str_end
    
    def __begin(self):
        self.__file.write("""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Report</title>
                <style>
                    .cloud {
                        display:none;
                        position:absolute;
                        background-color:grey;
                        color:white;
                        padding:10px;
                        box-shadow: 10px 5px 5px rgba(0,0,0,.6);
                        border-radius: 3px;
                    }
                    .show {
                        display:inline-block !important;
                    }
                    span {
                        display: inline-block;
                    }
                </style>
            </head>
            <body>
        """)
    
    def __end(self):
        self.__file.write('</html>')
        

class ChunckedReport:
    __dictname = None
    __current_report = None
    __writed_chunks = 0
    __elems_per_page = 30

    def __init__(self, dictname='report'):
        self.__dictname = dictname
    
    def write_coefs(self, sv, datetime, coefs):
        if(self.__writed_chunks % self.__elems_per_page == 0):
            self.__current_report = Report(self.__dictname + '/{0}.html'.format(int(self.__writed_chunks / self.__elems_per_page)))
        
        self.__current_report.write_coefs(sv, datetime, coefs)

        self.__writed_chunks += 1
    
    def __del__(self):
        index = open('index.html', 'r').read()
        index = index.replace('{{q_pages}}', str(int(self.__writed_chunks / self.__elems_per_page) + 1))
        open(self.__dictname + '/index.html', 'w').write(index)

def write_report(rinex_merged_data):
    r = ChunckedReport()
    for sv in rinex_merged_data:
        for datetime_k in rinex_merged_data[sv]:
            r.write_coefs(sv, datetime_k, rinex_merged_data[sv][datetime_k])