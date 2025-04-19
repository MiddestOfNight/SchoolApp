from flask import Flask

app = Flask(__name__)

@app.context_processor
def utility_processor():
    def get_score(scores, score_type, attempt=None):
        """Hàm helper lấy điểm theo loại và lần thử"""
        for score in scores:
            # Xử lý cả 2 định dạng: '15P_1' và '15P1'
            clean_type = score.score_type.replace('_', '')
            if clean_type.startswith(score_type):
                if attempt and str(attempt) in clean_type[len(score_type):]:
                    return score.score_value
                elif score_type == 'FINAL' and clean_type == 'FINAL':
                    return score.score_value
        return ""
    return dict(get_score=get_score)